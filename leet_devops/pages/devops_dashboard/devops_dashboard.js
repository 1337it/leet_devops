frappe.pages["devops_dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Leet DevOps Dashboard",
    single_column: true,
  });

  const $ = frappe.dom;
  const container = wrapper.querySelector("#output");
  const log = (msg) => {
    container.textContent =
      typeof msg === "string" ? msg : JSON.stringify(msg, null, 2);
  };

  // Create PR button
  wrapper.querySelector("#btn-create").addEventListener("click", async () => {
    const args = {
      repository: wrapper.querySelector("#repo").value,
      title: wrapper.querySelector("#title").value,
      description: wrapper.querySelector("#desc").value,
      files_json: wrapper.querySelector("#files").value,
    };

    try {
      const cr = await frappe.call({
        method: "leet_devops.api.devops.create_change_request",
        args,
      });
      const pr = await frappe.call({
        method: "leet_devops.api.devops.open_pr",
        args: { change_request: cr.message },
      });
      frappe.msgprint(`✅ Pull Request created: <a href="${pr.message}" target="_blank">${pr.message}</a>`);
      log(pr.message);
    } catch (e) {
      frappe.msgprint({ title: "Error", message: e.message });
      log(e.message);
    }
  });

  // Deploy button
  wrapper.querySelector("#btn-deploy").addEventListener("click", async () => {
    const args = {
      environment: wrapper.querySelector("#env").value,
      ref: wrapper.querySelector("#ref").value,
    };

    try {
      const r = await frappe.call({
        method: "leet_devops.api.devops.deploy",
        args,
      });
      frappe.msgprint(`🚀 Deployment triggered: ${r.message.status}`);
      log(r.message);
    } catch (e) {
      frappe.msgprint({ title: "Error", message: e.message });
      log(e.message);
    }
  });
};
