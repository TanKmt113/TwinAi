const ontologyData = {
  assets: [
    {
      id: "ELV-CALIDAS-01",
      name: "Thang máy Calidas 1",
      component: "Cáp kéo",
      remainingMonths: 5,
      sparePart: "Bộ cáp kéo Calidas",
      stock: 0,
      leadTimeMonths: 7,
      approver: "CEO",
      source: "Manual bảo trì thang máy - mục kiểm tra cáp kéo mỗi 6 tháng",
      evidence: ["Đường kính cáp", "Độ rung khi vận hành", "Ngày kiểm tra gần nhất"],
    },
    {
      id: "ELV-CALIDAS-02",
      name: "Thang máy Calidas 2",
      component: "Bộ điều khiển cửa",
      remainingMonths: 14,
      sparePart: "Module cửa Calidas",
      stock: 1,
      leadTimeMonths: 2,
      approver: "Giám đốc kỹ thuật",
      source: "Manual bảo trì thang máy - mục kiểm tra cửa tầng",
      evidence: ["Log lỗi cửa", "Tần suất kẹt cửa", "Ngày kiểm tra gần nhất"],
    },
    {
      id: "ELV-SERVICE-01",
      name: "Thang máy dịch vụ 1",
      component: "Motor kéo",
      remainingMonths: 8,
      sparePart: "Motor kéo 11kW",
      stock: 0,
      leadTimeMonths: 4,
      approver: "Giám đốc kỹ thuật",
      source: "Manual bảo trì thang máy - mục đo tải motor",
      evidence: ["Nhiệt độ motor", "Dòng tải", "Lịch sử bảo trì"],
    },
  ],
  rules: [
    {
      id: "R-001",
      name: "Cảnh báo linh kiện còn ≤ 6 tháng tuổi thọ",
      source: "Manual bảo trì thang máy",
      test: (asset) => asset.remainingMonths <= 6,
      action: "Tạo cảnh báo kỹ thuật và nhiệm vụ kiểm tra.",
    },
    {
      id: "R-002",
      name: "Tạo đề xuất mua hàng nếu tồn kho = 0 và lead time vượt thời gian còn lại",
      source: "Quy trình mua hàng + dữ liệu tồn kho",
      test: (asset) => asset.stock === 0 && asset.leadTimeMonths > asset.remainingMonths,
      action: "Tạo đề xuất mua hàng và xác định người phê duyệt.",
    },
    {
      id: "R-003",
      name: "Trả lời không đủ dữ liệu nếu câu hỏi ngoài Ontology mẫu",
      source: "Guardrail chống ảo giác",
      test: () => false,
      action: "Không suy đoán ngoài dữ liệu đã mô hình hóa.",
    },
  ],
};

let lastFindings = [];
let actionLog = [];

const assetRows = document.querySelector("#assetRows");
const ruleList = document.querySelector("#ruleList");
const actionLogEl = document.querySelector("#actionLog");
const responseBox = document.querySelector("#responseBox");
const questionForm = document.querySelector("#questionForm");
const questionInput = document.querySelector("#questionInput");
const runReasoningBtn = document.querySelector("#runReasoningBtn");
const clearActionsBtn = document.querySelector("#clearActionsBtn");
const riskCount = document.querySelector("#riskCount");
const taskCount = document.querySelector("#taskCount");
const purchaseCount = document.querySelector("#purchaseCount");

function getHealthBadge(asset) {
  if (asset.remainingMonths <= 6) {
    return `<span class="badge danger">${asset.remainingMonths} tháng</span>`;
  }
  if (asset.remainingMonths <= 9) {
    return `<span class="badge warn">${asset.remainingMonths} tháng</span>`;
  }
  return `<span class="badge ok">${asset.remainingMonths} tháng</span>`;
}

function renderAssets() {
  assetRows.innerHTML = ontologyData.assets
    .map(
      (asset) => `
        <tr>
          <td><strong>${asset.name}</strong><br><span class="muted">${asset.id}</span></td>
          <td>${asset.component}</td>
          <td>${getHealthBadge(asset)}</td>
          <td>${asset.stock} ${asset.stock > 0 ? "bộ" : "bộ"}</td>
          <td>${asset.leadTimeMonths} tháng</td>
        </tr>
      `,
    )
    .join("");
}

function renderRules() {
  ruleList.innerHTML = ontologyData.rules
    .map(
      (rule) => `
        <div class="rule-item">
          <strong>${rule.id}: ${rule.name}</strong>
          <p>Nguồn: ${rule.source}. Hành động: ${rule.action}</p>
        </div>
      `,
    )
    .join("");
}

function runReasoning() {
  const findings = ontologyData.assets.map((asset) => {
    const triggeredRules = ontologyData.rules.filter((rule) => rule.test(asset));
    return {
      asset,
      triggeredRules,
      needsInspection: triggeredRules.some((rule) => rule.id === "R-001"),
      needsPurchase: triggeredRules.some((rule) => rule.id === "R-002"),
    };
  });

  lastFindings = findings.filter((finding) => finding.triggeredRules.length > 0);
  actionLog = lastFindings.flatMap((finding) => buildActions(finding));
  renderActions();
  renderCounters();
  responseBox.innerHTML = buildRiskAnswer();
}

function buildActions(finding) {
  const actions = [];
  const { asset } = finding;

  if (finding.needsInspection) {
    actions.push({
      type: "Task kiểm tra",
      title: `Kiểm tra ${asset.component} của ${asset.name}`,
      detail: `Cần đo: ${asset.evidence.join(", ")}. Căn cứ: ${asset.source}.`,
    });
  }

  if (finding.needsPurchase) {
    actions.push({
      type: "Đề xuất mua hàng",
      title: `Mua ${asset.sparePart}`,
      detail: `Tồn kho hiện tại ${asset.stock}, lead time ${asset.leadTimeMonths} tháng, còn lại ${asset.remainingMonths} tháng. Người phê duyệt: ${asset.approver}.`,
    });
  }

  return actions;
}

function renderActions() {
  if (!actionLog.length) {
    actionLogEl.innerHTML = `<p class="empty-state">Chưa có hành động. Bấm "Chạy suy luận" để tạo log.</p>`;
    return;
  }

  actionLogEl.innerHTML = actionLog
    .map(
      (item) => `
        <div class="action-item">
          <strong>${item.type}: ${item.title}</strong>
          <p>${item.detail}</p>
        </div>
      `,
    )
    .join("");
}

function renderCounters() {
  const risks = lastFindings.length;
  const tasks = actionLog.filter((item) => item.type === "Task kiểm tra").length;
  const purchases = actionLog.filter((item) => item.type === "Đề xuất mua hàng").length;

  riskCount.textContent = risks;
  taskCount.textContent = tasks;
  purchaseCount.textContent = purchases;
}

function buildRiskAnswer() {
  if (!lastFindings.length) {
    return `<strong>Kết luận:</strong> Chưa phát hiện cảnh báo trong dữ liệu mẫu.`;
  }

  const details = lastFindings
    .map((finding) => {
      const { asset } = finding;
      const purchaseText = finding.needsPurchase
        ? `Tồn kho ${asset.stock}, lead time ${asset.leadTimeMonths} tháng nên cần tạo đề xuất mua hàng.`
        : "Chưa cần tạo đề xuất mua hàng từ dữ liệu hiện tại.";

      return `
        <p>
          <strong>${asset.name}</strong>: ${asset.component} còn ${asset.remainingMonths} tháng.
          Căn cứ: ${asset.source}. ${purchaseText}
        </p>
      `;
    })
    .join("");

  return `
    <strong>Kết luận:</strong> Có ${lastFindings.length} tài sản cần chú ý.
    ${details}
    <p><strong>Hành động đề xuất:</strong> tạo task kiểm tra, kiểm tra tồn kho phụ tùng, và trình phê duyệt nếu cần mua hàng.</p>
  `;
}

function answerQuestion(question) {
  const normalized = question.toLowerCase();
  if (!lastFindings.length) {
    runReasoning();
  }

  if (includesAny(normalized, ["thang máy", "linh kiện", "kiểm tra", "sắp cần", "sắp hỏng", "rủi ro"])) {
    return buildRiskAnswer();
  }

  if (includesAny(normalized, ["mua", "cáp", "đức", "lead time", "tồn kho"])) {
    const purchaseFinding = lastFindings.find((finding) => finding.needsPurchase);
    if (!purchaseFinding) {
      return `<strong>Kết luận:</strong> Không có đề xuất mua hàng nào trong dữ liệu mẫu hiện tại.`;
    }

    const { asset } = purchaseFinding;
    return `
      <strong>Kết luận:</strong> Cần đề xuất mua ${asset.sparePart}.
      <p><strong>Căn cứ:</strong> ${asset.component} của ${asset.name} còn ${asset.remainingMonths} tháng tuổi thọ, tồn kho hiện tại là ${asset.stock}, trong khi lead time mua hàng là ${asset.leadTimeMonths} tháng.</p>
      <p><strong>Hành động:</strong> tạo purchase request và trình ${asset.approver} phê duyệt.</p>
    `;
  }

  if (includesAny(normalized, ["phê duyệt", "duyệt", "approver", "ceo"])) {
    const approvalFinding = lastFindings.find((finding) => finding.needsPurchase);
    if (!approvalFinding) {
      return `<strong>Kết luận:</strong> Chưa có yêu cầu cần phê duyệt trong dữ liệu mẫu.`;
    }

    return `
      <strong>Kết luận:</strong> Người phê duyệt là ${approvalFinding.asset.approver}.
      <p><strong>Căn cứ:</strong> yêu cầu mua ${approvalFinding.asset.sparePart} được tạo từ quy tắc R-002 và quy trình mua hàng.</p>
    `;
  }

  if (includesAny(normalized, ["manual", "căn cứ", "nguồn", "evidence", "bằng chứng"])) {
    const sources = ontologyData.assets.map((asset) => `<li>${asset.name}: ${asset.source}</li>`).join("");
    return `
      <strong>Nguồn căn cứ trong demo:</strong>
      <ul>${sources}</ul>
      <p>LLM chỉ được diễn giải các nguồn này và các rule đã định nghĩa.</p>
    `;
  }

  return `
    <strong>Không đủ dữ liệu.</strong>
    <p>Câu hỏi này nằm ngoài Ontology mẫu của demo. Hệ thống không suy đoán vì chưa có thực thể, rule hoặc nguồn căn cứ liên quan.</p>
  `;
}

function includesAny(text, keywords) {
  return keywords.some((keyword) => text.includes(keyword));
}

questionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  responseBox.innerHTML = answerQuestion(questionInput.value.trim());
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    responseBox.innerHTML = answerQuestion(questionInput.value);
  });
});

runReasoningBtn.addEventListener("click", runReasoning);

clearActionsBtn.addEventListener("click", () => {
  actionLog = [];
  actionLogEl.innerHTML = `<p class="empty-state">Log hành động đã được xóa. Bấm "Chạy suy luận" để tạo lại.</p>`;
  taskCount.textContent = "0";
  purchaseCount.textContent = "0";
});

renderAssets();
renderRules();
renderCounters();
