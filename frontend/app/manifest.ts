import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Ancient Greek Reader",
    short_name: "Greek Reader",
    description: "Turn photographed or pasted Ancient Greek into Classical Attic audio.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f0e6",
    theme_color: "#172033",
  };
}
