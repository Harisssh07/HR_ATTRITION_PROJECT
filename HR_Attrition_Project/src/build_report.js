// Builds reports/HR_Attrition_Final_Report.docx  (run: node src/build_report.js)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle, Footer, PageNumber, PageBreak,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const NAVY = "1F2A44", BLUE = "2E86AB", RED = "E4572E", LIGHT = "EEF3F8", FONT = "Calibri";
const W = 9746; // content width (A4, 0.75" margins)

const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "model_summary.json")));

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 288 }, ...o.p,
  children: Array.isArray(t) ? t : [run(t, o.r)] });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t)] });
const bullets = (items) => items.map((t) => new Paragraph({
  numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 },
  children: Array.isArray(t) ? t : [run(t)] }));
const B = (t) => run(t, { bold: true });
const caption = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [run(t, { italics: true, size: 18, color: "5A6478" })] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

function img(rel, widthPx, aspect) {
  const data = fs.readFileSync(path.join(ROOT, rel));
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
    children: [new ImageRun({ type: "png", data, transformation: { width: widthPx, height: Math.round(widthPx * aspect) },
      altText: { title: rel, description: rel, name: rel } })] });
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "D5DCE8" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(header, rows, widths) {
  const mk = (txt, w, hdr, i) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: hdr ? { fill: NAVY, type: ShadingType.CLEAR, color: "auto" }
      : { fill: rows.indexOf(txt) % 2 ? "FFFFFF" : "F7F9FC", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({ children: [run(String(txt), hdr ? { bold: true, color: "FFFFFF", size: 20 } : { size: 20 })] })],
  });
  const trs = [new TableRow({ tableHeader: true, children: header.map((h, i) => mk(h, widths[i], true, i)) })];
  rows.forEach((r, ri) => trs.push(new TableRow({
    children: r.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA }, borders,
      shading: { fill: ri % 2 ? "FFFFFF" : "F7F9FC", type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 70, bottom: 70, left: 110, right: 110 },
      children: [new Paragraph({ children: [run(String(c), { size: 20 })] })] })) })));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
const gap = () => new Paragraph({ spacing: { after: 160 }, children: [] });

// ---------------------------------------------------------------------------------- content
const m = metrics.test_metrics_at_0_5 || metrics["test_metrics_at_0.5"];
const fmt = (x) => x.toFixed(2);
const modelRows = Object.entries(m).map(([k, v]) =>
  [k, fmt(v["Accuracy"]), fmt(v["Precision"]), fmt(v["Recall"]), fmt(v["F1-Score"]), fmt(v["ROC-AUC"])]);

const children = [
  // ---- cover
  new Paragraph({ spacing: { before: 2400, after: 120 }, children: [run("HR ANALYTICS", { size: 24, bold: true, color: RED, characterSpacing: 60 })] }),
  new Paragraph({ spacing: { after: 120 }, children: [run("Employee Attrition Prediction", { size: 64, bold: true, color: NAVY })] }),
  new Paragraph({ spacing: { after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 8 } },
    children: [run("Python · Scikit-learn · Power BI", { size: 30, color: "4A5568" })] }),
  new Paragraph({ spacing: { before: 240, after: 60 }, children: [run("Final Project Report", { size: 32, bold: true, color: NAVY })] }),
  P("Data Analyst portfolio project – end-to-end analysis of employee turnover, a machine-learning early-warning model and an interactive Power BI dashboard.",
    { r: { color: "4A5568", size: 22 } }),
  new Paragraph({ spacing: { before: 1800 }, children: [run("November 2026", { color: "4A5568" })] }),
  new Paragraph({ children: [run("Dataset: 1,470 employees (synthetic, IBM-HR-style structure)", { color: "4A5568", size: 20 })] }),
  pageBreak(),

  // ---- 1
  H1("1. Executive Summary"),
  P("Employee attrition is costly: every departure removes experience, disrupts teams and triggers recruitment and onboarding expense. This project analyses a 1,470-employee HR dataset to understand who leaves and why, builds a model that flags employees at risk of leaving, and delivers the results in an interactive Power BI dashboard."),
  table(["Headline metric", "Result"], [
    ["Employees analysed / left", "1,470 / 227"],
    ["Overall attrition rate", "15.4 %"],
    ["Overtime vs no overtime", "26.0 % vs 11.3 % (2.3× higher)"],
    ["Highest-risk groups", "Age 18–25 (34 %), pay below 6K/month (35–38 %), Sales Representatives (28 %), Laboratory Technicians (22 %)"],
    ["Best model", "Random Forest: ROC-AUC 0.81, accuracy 0.80, recall 0.56, precision 0.39, F1 0.46 (test set)"],
    ["Risk tiers (out-of-fold)", "Actual attrition 5.8 % (Low), 21.7 % (Medium), 45.4 % (High)"],
  ], [3200, 6546]),
  gap(),
  P([B("Key message: "), run("attrition is concentrated, not random. It clusters among early-career, lower-paid employees who work overtime, so targeted retention actions are likely to outperform company-wide programmes.")]),
  P([B("Data caveat: "), run("the dataset is synthetic (generated with research-based relationships so the project is reproducible offline). Findings describe this dataset and should be re-validated on real company data before decisions are made.")]),

  // ---- 2
  H1("2. Problem Statement and Objectives"),
  P("HR teams usually learn about resignations after the fact. The objective is to move from reactive reporting to proactive, data-driven retention."),
  ...bullets([
    "Analyse employee data to understand attrition patterns.",
    "Identify the factors that influence employee turnover.",
    "Predict whether an employee is likely to leave using machine learning.",
    "Visualise HR insights in an interactive Power BI dashboard.",
    "Support HR with data-driven retention decisions.",
  ]),

  // ---- 3
  H1("3. Data Description"),
  P("The raw file contains 1,490 records and 32 columns, grouped as follows. The target variable is Attrition (Yes/No)."),
  table(["Group", "Variables"], [
    ["Demographics", "Age, Gender, MaritalStatus, Education, EducationField"],
    ["Job & organisation", "Department, JobRole, JobLevel, BusinessTravel, OverTime, DistanceFromHome"],
    ["Compensation", "MonthlyIncome, PercentSalaryHike, StockOptionLevel"],
    ["Experience & tenure", "TotalWorkingYears, YearsAtCompany, YearsInCurrentRole, YearsSinceLastPromotion, YearsWithCurrManager, NumCompaniesWorked"],
    ["Engagement", "JobSatisfaction, EnvironmentSatisfaction, RelationshipSatisfaction, WorkLifeBalance, JobInvolvement, PerformanceRating, TrainingTimesLastYear"],
    ["Target", "Attrition (Yes/No), converted to Attrition_Flag (1/0)"],
  ], [2400, 7346]),
  gap(),
  P("Data provenance: because the project had to run offline and be fully reproducible, the data is simulated by src/generate_dataset.py. Attrition is drawn from a logistic model in which overtime, low satisfaction, low pay, short tenure, frequent travel, long commutes and similar factors raise risk. Dirty data (missing values, duplicates, inconsistent text) was injected deliberately so that the cleaning stage reflects real-world work. A real export with the same column names can be dropped in and the whole pipeline re-run."),

  // ---- 4
  H1("4. Data Cleaning and Preprocessing"),
  table(["Issue found", "Treatment", "Result"], [
    ["20 exact duplicate records", "drop_duplicates on all columns and EmployeeID", "1,490 → 1,470 rows"],
    ["68 missing cells (income, satisfaction, experience, travel)", "Income: median by job level; experience: median by age band; others: median / mode", "0 missing"],
    ["Inconsistent text (' SALES ', lower-case roles)", "Trim whitespace; unify to most frequent spelling", "3 departments, 10 roles"],
    ["3 constant columns (EmployeeCount, Over18, StandardHours)", "Dropped (no information)", "32 → 29 columns"],
    ["Illogical values (tenure > total experience)", "Capped to valid range", "Consistent dates"],
    ["Raw numeric codes", "Engineered AgeGroup, SalaryBand, ExperienceBand, TenureBand and readable labels with sort keys", "Power BI-ready"],
  ], [3300, 4146, 2300]),
  gap(),
  P([B("Encoding and scaling. "), run("Categorical features were one-hot encoded. Numeric features were standardised only for Logistic Regression, which is sensitive to feature scale; tree-based models are scale-invariant and were left unscaled.")]),

  // ---- 5
  H1("5. Exploratory Data Analysis"),
  P("Attrition rate = employees who left ÷ employees in the group. The dashed line in each chart marks the company average of 15.4 %; red bars are above average."),
  H2("5.1 Overtime is the clearest behavioural driver"),
  img("images/eda/08_overtime.png", 330, 650 / 800),
  caption("Figure 1 – Attrition: overtime vs no overtime (26.0 % vs 11.3 %)"),
  P("The overtime effect compounds with dissatisfaction: the heat-map below shows attrition is highest where overtime meets low job satisfaction."),
  img("images/eda/12_overtime_satisfaction.png", 380, 620 / 832),
  caption("Figure 2 – Attrition (%) by job satisfaction and overtime"),
  H2("5.2 Pay and age"),
  img("images/eda/06_salary_band.png", 520, 650 / 1175),
  caption("Figure 3 – Attrition by monthly salary band: 35–38 % below 6K versus 5.6 % above 12K"),
  img("images/eda/05_age_group.png", 520, 650 / 1175),
  caption("Figure 4 – Attrition by age group: 34 % for 18–25, under 5 % for 46+"),
  H2("5.3 Job role"),
  img("images/eda/04_job_role.png", 560, 726 / 1326),
  caption("Figure 5 – Attrition by job role (n = employees in the role)"),
  H2("5.4 Summary of EDA findings"),
  table(["Dimension", "Finding"], [
    ["Department", "Sales highest at 18.3 %; R&D 14.2 % and HR 14.3 % are near the company average."],
    ["Gender", "Female 17.3 % vs male 14.2 %; a small gap likely within sampling noise, so monitor rather than act."],
    ["Job role", "Sales Representative 28.1 %, Laboratory Technician 21.7 %; senior/managerial roles 3–6 %."],
    ["Age", "Sharp decline with age: 34 % (18–25) → 4 % (46+)."],
    ["Salary", "Below 6K per month: 35–38 %; 12K+: 5.6 %."],
    ["Job satisfaction", "Low satisfaction 22.2 % versus 11.6–14.4 % for the other levels."],
    ["Experience", "0–5 years of experience ≈ 31 %; 20+ years 7 %."],
    ["Correlations", "Strongest negative correlations with attrition: JobLevel (−0.26), Age (−0.22), TotalWorkingYears (−0.21), YearsAtCompany (−0.19)."],
  ], [2300, 7446]),
  gap(),

  // ---- 6
  H1("6. Machine Learning – Attrition Prediction"),
  H2("6.1 Approach"),
  ...bullets([
    [B("Models: "), run("Logistic Regression (explainable baseline), Decision Tree (interpretable), Random Forest (ensemble).")],
    [B("Split: "), run("stratified 80/20 (1,176 train / 294 test) to preserve the 15 % minority class.")],
    [B("Imbalance: "), run("class-weight balancing; accuracy alone is misleading because predicting “nobody leaves” scores about 85 %.")],
    [B("Tuning: "), run("5-fold grid search optimising F1 on the training set only; the model was selected on cross-validated F1, never on the test set.")],
    [B("Decision threshold: "), run("chosen on out-of-fold training predictions (result: 0.50).")],
  ]),
  H2("6.2 Results on the unseen test set"),
  table(["Model", "Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"], modelRows, [2746, 1400, 1400, 1400, 1400, 1400]),
  gap(),
  img("images/model/22_model_comparison.png", 520, 693 / 1325),
  caption("Figure 6 – Model comparison (test set)"),
  img("images/model/20_confusion_matrices.png", 620, 649 / 2158),
  caption("Figure 7 – Confusion matrices (test set)"),
  P([B("Interpretation. "), run("Random Forest is the best overall (highest accuracy, precision, F1 and ROC-AUC). Logistic Regression catches more leavers (recall 0.73) but flags many more people incorrectly (precision 0.27). If HR prefers to cast a wider net and accept more false alarms, Logistic Regression at its default threshold is a reasonable alternative; if reviewer time is scarce, Random Forest is better. Precision of roughly 0.4 means about four in ten flagged employees genuinely leave, which suits an early-warning list for supportive conversations but not punitive decisions.")]),
  H2("6.3 What drives the predictions?"),
  img("images/model/23_feature_importance.png", 440, 876 / 1179),
  caption("Figure 8 – Random Forest feature importance (one-hot columns aggregated)"),
  P("Compensation and seniority (MonthlyIncome, JobLevel, TotalWorkingYears, Age) dominate, followed by overtime, time in role, commute distance and job role – consistent with the EDA. Importance shows what the model uses, not causation."),
  H2("6.4 Predictions exported for Power BI"),
  P("Each employee was scored with 5-fold out-of-fold probabilities: the model that scores an employee never saw that employee in training, so dashboard numbers are not inflated by memorisation. Probabilities are banded into Low (< 30 %), Medium (30–60 %) and High (≥ 60 %) risk."),
  table(["Risk tier", "Employees", "Actual attrition rate"], [
    ["Low", "791", "5.8 %"], ["Medium", "538", "21.7 %"], ["High", "141", "45.4 %"],
  ], [3200, 3200, 3346]),
  gap(),
  P("The High tier leaves at roughly eight times the rate of the Low tier, which is what HR needs to prioritise attention. Across all employees the out-of-fold model catches 108 of 227 leavers (recall 48 %) with 163 false alarms (precision 40 %); these full-population figures are slightly lower than the single test split, which is the more optimistic and noisier estimate (294 employees, about 45 leavers)."),

  // ---- 7
  H1("7. Power BI Dashboard"),
  P("The dashboard has three pages, all sharing five synchronised slicers (Department, Gender, Job Role, Age Group, Education). The images below are design previews rendered from the real prediction file; the Power BI build guide, 30+ DAX measures and an importable theme are provided in the powerbi folder."),
  table(["Page", "Content"], [
    ["1. Executive Overview", "Cards: Total Employees, Employees Who Left, Attrition Rate, Average Age. Department, Gender and Job Role attrition."],
    ["2. Attrition Drivers", "Salary-wise attrition, job-satisfaction analysis, overtime impact, experience analysis, education and age group."],
    ["3. Predicted Attrition", "Predicted leavers, high-risk headcount, model precision/recall, risk-tier charts, actual vs predicted by department, high-risk watch-list."],
  ], [2600, 7146]),
  gap(),
  img("powerbi/preview/dashboard_page1_preview.png", 600, 990 / 1760),
  caption("Figure 9 – Page 1: Executive Overview (design preview)"),
  img("powerbi/preview/dashboard_page2_preview.png", 600, 990 / 1760),
  caption("Figure 10 – Page 2: Attrition Drivers (design preview)"),
  img("powerbi/preview/dashboard_page3_preview.png", 600, 990 / 1760),
  caption("Figure 11 – Page 3: Predicted Attrition (design preview)"),

  // ---- 8
  H1("8. Business Recommendations"),
  P("These are hypotheses suggested by the data; patterns are correlations, so pilot and measure before scaling."),
  table(["Finding", "Suggested action"], [
    ["Overtime doubles attrition, worst with low satisfaction", "Review workload and staffing in overtime-heavy teams; cap sustained overtime; compensate or rotate it."],
    ["Pay below 6K/month and young employees leave most", "Benchmark entry-level pay; create early-career progression paths and retention bonuses."],
    ["Sales Representatives and Lab Technicians are hotspots", "Role-specific reviews: quotas and commissions for sales, shift patterns and career ladders for technicians."],
    ["Low satisfaction lifts attrition", "Act on survey results quickly; manager coaching; stay interviews."],
    ["High-risk tier = 141 employees at 45 % real attrition", "Give managers a monthly watch-list for supportive stay conversations; track whether outcomes improve."],
  ], [4000, 5746]),
  gap(),

  // ---- 9
  H1("9. Limitations and Future Work"),
  ...bullets([
    "Synthetic data: relationships are built in, so results validate the pipeline, not real-world effects. Re-run on actual HR data.",
    "Moderate precision and a small test set; confidence intervals and repeated cross-validation would quantify uncertainty.",
    "Model explains correlation, not causation; use A/B-tested interventions to prove retention actions work.",
    "Fairness: audit predictions by gender, age and other protected attributes before operational use; consider excluding sensitive features.",
    "Next steps: SHAP explanations, gradient boosting, probability calibration, scheduled refresh in Power BI Service, cost-of-attrition what-if analysis.",
  ]),

  // ---- 10
  H1("10. Conclusion"),
  P("The project demonstrates the complete analytics workflow: cleaning raw HR data, uncovering attrition drivers, building and honestly evaluating predictive models, and communicating results through a dashboard. Overtime, compensation, age/tenure and role consistently emerge as the factors most associated with attrition, and the model’s risk tiers separate employees into meaningfully different likelihoods of leaving, giving HR a practical, prioritised starting point for retention."),

  // ---- appendix
  H1("Appendix – Project Files and How to Run"),
  table(["Item", "Location"], [
    ["Raw / cleaned / prediction data", "data/raw, data/processed (attrition_predictions.csv feeds Power BI)"],
    ["Notebooks", "notebooks/01_Data_Cleaning_and_EDA.ipynb, 02_Attrition_Prediction_Model.ipynb"],
    ["Source code", "src/ (generate_dataset, data_cleaning, eda, model_training, run_pipeline)"],
    ["Model", "models/attrition_model.joblib (pipeline + threshold)"],
    ["Power BI kit", "powerbi/ (guide, DAX measures, theme, previews)"],
    ["Run everything", "pip install -r requirements.txt  then  python src/run_pipeline.py"],
  ], [3200, 6546]),
];

const doc = new Document({
  creator: "HR Analytics Project", title: "HR Analytics – Employee Attrition Prediction",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 34, bold: true, color: NAVY },
        paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, color: BLUE },
        paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [run("HR Analytics – Employee Attrition Prediction   |   Page ", { size: 18, color: "8D99AE" }),
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "8D99AE" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "reports", "HR_Attrition_Final_Report.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
