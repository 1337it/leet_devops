// Leet DevOps bundle entry
// This script loads at Desk startup via hooks.py

console.log("✅ Leet DevOps loaded: GitHub + SSH + OpenAI integration active.");

// Optional: small helper to show a notice when app is loaded

  frappe.msgprint({
    title: "Leet DevOps",
    message: "Leet DevOps app initialized successfully.",
    indicator: "green"
  });
