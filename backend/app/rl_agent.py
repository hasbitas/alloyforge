from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.distributions import Normal
from torch.nn import functional as F

from .config import settings
from .schemas import TargetProperties


@dataclass
class Rollout:
    states: Tensor
    raw_actions: Tensor
    old_log_probs: Tensor
    rewards: Tensor


class ActorCritic(nn.Module):
    def __init__(self, element_count: int) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(3, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(64, element_count)
        self.critic = nn.Linear(64, 1)
        self.log_std = nn.Parameter(torch.full((element_count,), -0.35))

    def forward(self, state: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        hidden = self.backbone(state)
        return self.actor_mean(hidden), self.log_std.exp().expand_as(self.actor_mean(hidden)), self.critic(hidden)


class PPOAlloyAgent:
    """Alloy design agent using PyTorch PPO.

    Continuous raw actions pass through a sigmoid gate. A threshold of 0.5
    selects active elements, whose weights are L1-normalized into fractions.
    """

    def __init__(
        self, elements: list[str], seed: int | None = None, device: str | None = None
    ) -> None:
        self.elements = elements
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        torch.manual_seed(seed if seed is not None else settings.random_seed)
        self.policy = ActorCritic(len(elements)).to(self.device)
        self.optimizer = torch.optim.Adam(
            self.policy.parameters(), lr=settings.ppo_learning_rate
        )

    @staticmethod
    def encode_targets(targets: TargetProperties) -> Tensor:
        return torch.tensor(
            [
                targets.temperature_c / 1500.0,
                targets.density_g_cm3 / 12.0,
                targets.strength_mpa / 2500.0,
            ],
            dtype=torch.float32,
        )

    def sample(self, targets: TargetProperties, count: int) -> tuple[list[dict[str, float]], Rollout]:
        state = self.encode_targets(targets).to(self.device).repeat(count, 1)
        with torch.no_grad():
            means, stds, _ = self.policy(state)
            distribution = Normal(means, stds)
            raw_actions = distribution.sample()
            log_probs = distribution.log_prob(raw_actions).sum(dim=1)

        compositions = [self._to_composition(row) for row in raw_actions]
        rollout = Rollout(
            states=state,
            raw_actions=raw_actions,
            old_log_probs=log_probs,
            rewards=torch.empty(count, device=self.device),
        )
        return compositions, rollout

    def _to_composition(self, raw_action: Tensor) -> dict[str, float]:
        gate_probability = torch.sigmoid(raw_action)
        gates = gate_probability >= 0.5
        if int(gates.sum()) < 2:
            gates[torch.topk(gate_probability, k=2).indices] = True
        positive_weights = F.softplus(raw_action) * gates
        fractions = positive_weights / positive_weights.abs().sum().clamp_min(1e-8)
        return {
            element: round(float(fraction), 6)
            for element, fraction in zip(self.elements, fractions, strict=True)
            if float(fraction) > 0
        }

    def update(self, rollout: Rollout, rewards: list[float], epochs: int = 4) -> float:
        reward_tensor = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        rollout.rewards = reward_tensor
        normalized = (reward_tensor - reward_tensor.mean()) / (
            reward_tensor.std(unbiased=False) + 1e-8
        )
        final_loss = torch.tensor(0.0, device=self.device)

        for _ in range(epochs):
            means, stds, values = self.policy(rollout.states)
            distribution = Normal(means, stds)
            new_log_probs = distribution.log_prob(rollout.raw_actions).sum(dim=1)
            ratio = (new_log_probs - rollout.old_log_probs).exp()
            advantage = normalized - values.squeeze(1).detach()
            unclipped = ratio * advantage
            clipped = ratio.clamp(1 - settings.ppo_clip, 1 + settings.ppo_clip) * advantage
            actor_loss = -torch.minimum(unclipped, clipped).mean()
            critic_loss = F.mse_loss(values.squeeze(1), normalized)
            entropy_bonus = distribution.entropy().sum(dim=1).mean()
            final_loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy_bonus

            self.optimizer.zero_grad(set_to_none=True)
            final_loss.backward()
            nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
            self.optimizer.step()

        return round(float(final_loss.detach().cpu()), 6)

