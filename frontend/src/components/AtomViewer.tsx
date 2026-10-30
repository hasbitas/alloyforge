import { useEffect, useRef } from "react";
import * as $3Dmol from "3dmol";

import { artifactUrl } from "../api";

interface AtomViewerProps {
  cifPath?: string;
}

export function AtomViewer({ cifPath }: AtomViewerProps) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!host.current) return;
    host.current.innerHTML = "";
    const viewer = $3Dmol.createViewer(host.current, {
      backgroundColor: "#101a18",
      antialias: true,
    });

    if (!cifPath) {
      viewer.addSphere({
        center: { x: 0, y: 0, z: 0 },
        radius: 1.2,
        color: "#b8ff65",
        opacity: 0.85,
      });
      viewer.addSphere({
        center: { x: 2.1, y: 0.4, z: 0 },
        radius: 0.75,
        color: "#62e8ff",
        opacity: 0.85,
      });
      viewer.addSphere({
        center: { x: -1.5, y: 1.2, z: 0.2 },
        radius: 0.62,
        color: "#ffb657",
        opacity: 0.85,
      });
      viewer.zoomTo();
      viewer.render();
      viewer.spin("y", 0.7);
      return () => viewer.clear();
    }

    fetch(artifactUrl(cifPath))
      .then((response) => response.text())
      .then((cif) => {
        viewer.addModel(cif, "cif");
        viewer.setStyle(
          {},
          {
            sphere: {
              scale: 0.42,
              colorscheme: {
                prop: "b",
                gradient: new $3Dmol.Gradient.RWB(-1, 1),
              },
            },
            stick: { radius: 0.12, color: "#c7d6d1" },
          },
        );
        viewer.addUnitCell();
        viewer.zoomTo();
        viewer.render();
        viewer.spin("y", 0.55);
      });

    return () => viewer.clear();
  }, [cifPath]);

  return <div className="atom-viewer" ref={host} aria-label="3D atomic structure" />;
}

