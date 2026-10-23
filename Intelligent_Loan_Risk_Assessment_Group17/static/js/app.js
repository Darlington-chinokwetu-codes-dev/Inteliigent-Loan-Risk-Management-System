const browserStorage = {
    getItem(key) { try { return localStorage.getItem(key); } catch { return null; } },
    setItem(key, value) { try { localStorage.setItem(key, value); } catch { showStorageNotice(); } },
    removeItem(key) { try { localStorage.removeItem(key); } catch { showStorageNotice(); } }
};
function showStorageNotice() {
    if (document.querySelector('#storage-notice')) return;
    const notice = document.createElement('p'); notice.id = 'storage-notice'; notice.className = 'alert'; notice.setAttribute('role', 'status');
    notice.textContent = 'Browser storage is unavailable. Your assessment still works, but history and preferences may not be saved.';
    document.querySelector('main').prepend(notice);
}
function readHistory(key) {
    try {
        const value = JSON.parse(browserStorage.getItem(key) || '[]');
        return Array.isArray(value) ? value.filter(item => item && Array.isArray(item.applicants) && item.applicants.every(applicant => applicant && Number.isFinite(applicant.default_probability) && Number.isFinite(applicant.loan_to_income_ratio))) : [];
    } catch { return []; }
}
document.querySelectorAll(".distribution-chart").forEach((chart) => {
    const cells = chart.querySelector(".history-cells");
    const marker = chart.querySelector(".applicant-marker");
    if (!cells || !marker) return;

    const points = JSON.parse(cells.dataset.cells || "[]");
    const maxCount = Math.max(1, ...points.map((point) => point.count));
    const svgNamespace = "http://www.w3.org/2000/svg";

    points.forEach((point) => {
        const circle = document.createElementNS(svgNamespace, "circle");
        const x = 74 + point.x * 462;
        const y = 22 + (1 - point.y) * 246;
        circle.setAttribute("cx", x.toFixed(1));
        circle.setAttribute("cy", y.toFixed(1));
        circle.setAttribute("r", (4 + 12 * Math.sqrt(point.count / maxCount)).toFixed(1));
        circle.setAttribute("fill-opacity", (0.28 + 0.62 * point.count / maxCount).toFixed(2));
        circle.classList.add("history-point");

        const title = document.createElementNS(svgNamespace, "title");
        title.textContent = `${point.count} historical records`;
        circle.append(title);
        cells.append(circle);
    });

    const markerX = 74 + Number(marker.dataset.x) * 462;
    const markerY = 22 + (1 - Number(marker.dataset.y)) * 246;
    marker.setAttribute("transform", `translate(${markerX.toFixed(1)} ${markerY.toFixed(1)})`);
});

const themeToggle = document.querySelector("#theme-toggle");
if (themeToggle) {
    const themeIcon = themeToggle.querySelector(".theme-toggle-icon");
    const themeLabel = themeToggle.querySelector(".theme-toggle-label");
    const setTheme = (theme) => {
        document.documentElement.dataset.theme = theme;
        const isDark = theme === "dark";
        themeToggle.setAttribute("aria-pressed", String(isDark));
        themeLabel.textContent = isDark ? "Light mode" : "Dark mode";
        themeIcon.textContent = isDark ? "☀" : "☾";
        document.querySelector('meta[name="theme-color"]')
            .setAttribute("content", isDark ? "#101a2b" : "#102a43");
    };

    setTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
    themeToggle.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        setTheme(nextTheme);
        browserStorage.setItem("loanrisk-theme", nextTheme);
    });
}

const assessmentForm = document.querySelector("#assessment-form");
if (assessmentForm) {
    const purpose = assessmentForm.querySelector("#loan-purpose");
    const secondarySection = assessmentForm.querySelector("#secondary-applicant");
    const otherLoanSection = assessmentForm.querySelector("#other-loan-details");
    const otherLoanType = otherLoanSection.querySelector('[name="other_loan_type"]');
    const secondaryInputs = secondarySection.querySelectorAll("input, select");
    const interestField = assessmentForm.querySelector("#model-interest-field");
    const interestInput = interestField.querySelector("input");
    const gradeField = assessmentForm.querySelector("#model-grade-field");
    const gradeInput = gradeField.querySelector("select");
    const submitButton = assessmentForm.querySelector("#submit-assessment");
    const instructions = assessmentForm.querySelector("#form-instructions");

    const updateSecondaryRequirement = () => {
        const educationSelected = purpose.value === "EDUCATION";
        const otherSelected = purpose.value === "OTHER";
        secondarySection.hidden = !educationSelected;
        secondaryInputs.forEach((input) => {
            input.required = educationSelected;
        });
        otherLoanSection.hidden = !otherSelected;
        otherLoanType.required = otherSelected;
        interestField.hidden = otherSelected;
        interestInput.required = !otherSelected;
        gradeField.hidden = otherSelected;
        gradeInput.required = !otherSelected;
        submitButton.textContent = otherSelected ? "Preview Loan Details" : "Assess Loan Risk";
        instructions.textContent = otherSelected
            ? "Specify the loan type to record its application details."
            : "Choose a loan purpose to see the relevant next steps.";
    };

    purpose.addEventListener("change", updateSecondaryRequirement);
    assessmentForm.addEventListener("reset", () => {
        window.setTimeout(updateSecondaryRequirement, 0);
    });
    updateSecondaryRequirement();
}

const historyEntryElement = document.querySelector("#assessment-history-entry");
if (historyEntryElement) {
    const storageKey = "loanrisk-assessment-history-v1";
    const entry = JSON.parse(historyEntryElement.textContent);
    const savedHistory = readHistory(storageKey);
    if (!savedHistory.some((item) => item.id === entry.id)) {
        savedHistory.push(entry);
        browserStorage.setItem(storageKey, JSON.stringify(savedHistory.slice(-100)));
    }
}

const historyCount = document.querySelector("#history-count");
if (historyCount) {
    const storageKey = "loanrisk-assessment-history-v1";
    const savedHistory = readHistory(storageKey);
    const assessments = savedHistory
        .filter((item) => Array.isArray(item.applicants) && item.assessed_at)
        .sort((first, second) => new Date(first.assessed_at) - new Date(second.assessed_at));
    const rows = document.querySelector("#history-rows");
    historyCount.textContent = assessments.length.toLocaleString();

    const appendCell = (row, text) => {
        const cell = document.createElement("td");
        cell.textContent = text;
        row.append(cell);
    };

    assessments.slice().reverse().forEach((assessment) => {
        assessment.applicants.forEach((applicant) => {
            const row = document.createElement("tr");
            row.dataset.risk = applicant.risk_category;
            const date = new Date(assessment.assessed_at);
            row.dataset.date = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
            appendCell(row, new Date(assessment.assessed_at).toLocaleString());
            appendCell(row, applicant.label);
            appendCell(row, `${(Number(applicant.loan_to_income_ratio) * 100).toFixed(1)}%`);
            appendCell(row, `${Number(applicant.default_probability).toFixed(2)}%`);
            appendCell(row, applicant.risk_category);
            const action = document.createElement('td');
            const remove = document.createElement('button');
            remove.type = 'button'; remove.className = 'secondary'; remove.textContent = 'Delete';
            remove.setAttribute('aria-label', `Delete assessment from ${date.toLocaleString()}`);
            remove.addEventListener('click', () => {
                if (!window.confirm('Delete this assessment and all its applicant estimates?')) return;
                browserStorage.setItem(storageKey, JSON.stringify(readHistory(storageKey).filter(item => item.id !== assessment.id)));
                window.location.reload();
            });
            action.append(remove); row.append(action);
            rows.append(row);
        });
    });

    const filterHistory = () => {
        const risk = document.querySelector('#history-risk').value;
        const from = document.querySelector('#history-from').value;
        const to = document.querySelector('#history-to').value;
        let visible = 0;
        rows.querySelectorAll('tr').forEach(row => {
            row.hidden = Boolean((risk && risk !== row.dataset.risk) || (from && row.dataset.date < from) || (to && row.dataset.date > to));
            if (!row.hidden) visible++;
        });
        document.querySelector('#history-filter-status').textContent = `${visible} applicant estimates shown. Charts include all saved assessments.`;
    };
    document.querySelectorAll('.history-filters select, .history-filters input').forEach(field => field.addEventListener('change', filterHistory));
    filterHistory();
    if (!assessments.length) {
        const start = document.createElement('a'); start.href = '/'; start.className = 'button-link'; start.textContent = 'Start an assessment';
        document.querySelector('#history-filter-status').after(start);
    }

    const emptyMessage = "No saved assessments yet. Complete an assessment to start building your private chart history.";
    const svgNamespace = "http://www.w3.org/2000/svg";
    const createChart = (containerId, metricKey, metricLabel, formatValue, maxValue) => {
        const container = document.querySelector(`#${containerId}`);
        if (!assessments.length) {
            const message = document.createElement("p");
            message.className = "empty-history";
            message.textContent = emptyMessage;
            container.append(message);
            return;
        }

        const chartWidth = 760;
        const chartHeight = 250;
        const margin = { top: 18, right: 24, bottom: 42, left: 62 };
        const plotWidth = chartWidth - margin.left - margin.right;
        const plotHeight = chartHeight - margin.top - margin.bottom;
        const values = assessments.flatMap((assessment) => assessment.applicants
            .map((applicant) => Number(applicant[metricKey]))
            .filter(Number.isFinite));
        const upperBound = maxValue || Math.max(0.1, Math.ceil(Math.max(...values) * 10) / 10);
        const svg = document.createElementNS(svgNamespace, "svg");
        svg.setAttribute("viewBox", `0 0 ${chartWidth} ${chartHeight}`);
        svg.setAttribute("role", "img");
        svg.setAttribute("aria-label", `${metricLabel} for saved assessments`);

        [0, 0.5, 1].forEach((fraction) => {
            const y = margin.top + plotHeight * (1 - fraction);
            const line = document.createElementNS(svgNamespace, "line");
            line.setAttribute("x1", margin.left);
            line.setAttribute("x2", chartWidth - margin.right);
            line.setAttribute("y1", y);
            line.setAttribute("y2", y);
            line.classList.add("history-grid-line");
            svg.append(line);

            const label = document.createElementNS(svgNamespace, "text");
            label.setAttribute("x", margin.left - 9);
            label.setAttribute("y", y + 4);
            label.setAttribute("text-anchor", "end");
            label.textContent = formatValue(upperBound * fraction);
            svg.append(label);
        });

        const applicantTypes = [
            { label: "Primary applicant", key: "Primary applicant", className: "primary-series" },
            { label: "Secondary applicant", key: "Secondary applicant", className: "secondary-series" },
        ];
        applicantTypes.forEach((type) => {
            const points = [];
            assessments.forEach((assessment, index) => {
                const applicant = assessment.applicants.find((item) => item.label === type.key);
                if (!applicant) return;
                const value = Number(applicant[metricKey]);
                if (!Number.isFinite(value)) return;
                points.push({
                    x: margin.left + (assessments.length < 2 ? plotWidth / 2 : (index / (assessments.length - 1)) * plotWidth),
                    y: margin.top + plotHeight * (1 - Math.min(value / upperBound, 1)),
                    value,
                    assessment,
                    applicant,
                });
            });
            if (!points.length) return;

            points.forEach((point) => {
                const circle = document.createElementNS(svgNamespace, "circle");
                circle.setAttribute("cx", point.x);
                circle.setAttribute("cy", point.y);
                circle.setAttribute("r", 4);
                circle.classList.add("history-marker", type.className);
                const title = document.createElementNS(svgNamespace, "title");
                title.textContent = `${new Date(point.assessment.assessed_at).toLocaleString()} · ${type.label}: ${formatValue(point.value)}`;
                circle.append(title);
                svg.append(circle);
            });
        });

        const axisLabel = document.createElementNS(svgNamespace, "text");
        axisLabel.setAttribute("x", chartWidth / 2);
        axisLabel.setAttribute("y", chartHeight - 8);
        axisLabel.setAttribute("text-anchor", "middle");
        axisLabel.textContent = "Assessments (oldest to newest)";
        svg.append(axisLabel);
        container.append(svg);

        const legend = document.createElement("div");
        legend.className = "history-legend";
        applicantTypes.forEach((type) => {
            if (assessments.some((assessment) => assessment.applicants.some((item) => item.label === type.key))) {
                const item = document.createElement("span");
                item.className = type.className;
                item.textContent = type.label;
                legend.append(item);
            }
        });
        container.append(legend);
    };

    createChart("ratio-chart", "loan_to_income_ratio", "Loan-to-income ratio", (value) => `${(value * 100).toFixed(0)}%`);
    createChart("probability-chart", "default_probability", "Estimated default probability", (value) => `${value.toFixed(0)}%`, 100);

    document.querySelector("#clear-history").addEventListener("click", () => {
        if (window.confirm("Clear all assessment metrics saved in this browser?")) {
            browserStorage.removeItem(storageKey);
            window.location.reload();
        }
    });
}
