import React from "react";
import { createRoot } from "react-dom/client";
import { Greeting } from "./components/Greeting";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root was not found");
}

createRoot(rootElement).render(
  <React.StrictMode>
    <Greeting name="Apxoh" />
  </React.StrictMode>,
);
