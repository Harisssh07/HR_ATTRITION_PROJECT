# Power BI Dashboard – Build Guide (≈ 60–90 minutes)

> A `.pbix` file can only be authored inside **Power BI Desktop**, so this folder gives you everything needed to
> build it quickly and exactly: cleaned data, ready-made DAX, an importable theme, a page-by-page layout and
> design previews (`preview/`) rendered from the real data.

## 1. Load the data
1. **Home → Get Data → Text/CSV** → `data/processed/attrition_predictions.csv` → **Transform Data**.
2. In Power Query: confirm types (`Age`, `MonthlyIncome`… = Whole Number; `Attrition_Probability` = Decimal). Rename the query **`HR`**. **Close & Apply**.
3. **View → Themes → Browse for themes** → `powerbi/HR_Analytics_Theme.json`.
4. Create an empty table `_Measures` (Home → Enter Data) and paste the measures from `DAX_Measures.dax` (one measure at a time: *New measure*).

## 2. Model housekeeping (Data view → Column tools → *Sort by column*)
| Column | Sort by |
|---|---|
| `AgeGroup` | `AgeGroup_Sort` |
| `SalaryBand` | `SalaryBand_Sort` |
| `ExperienceBand` | `ExperienceBand_Sort` |
| `EducationLevel` | `Education_Sort` |
| `JobSatisfactionLevel` | `JobSatisfaction` |
| `Risk_Level` | `Risk_Sort` |

Hide helper columns (`*_Sort`, `Attrition_Flag`, `Risk_Sort`) from Report view. Set `Attrition_Probability` to *Percentage*.
Optional: add a What-If parameter **Replacement Cost %** (0.3–2.0, step 0.1, default 0.5) for the cost measures.

## 3. Pages and visuals
Canvas 16:9 (1280×720). Page background `#F3F6FA` (set by the theme). Header: rectangle `#1F2A44`, white title text.
Sync the **five slicers** across all pages: *View → Sync slicers*.

### Slicers (all pages, top row) – tile style, dropdown
`Department` · `Gender` · `JobRole` · `AgeGroup` · `EducationLevel`

### Page 1 – Executive Overview
| # | Requirement | Visual | Fields |
|---|---|---|---|
| 1 | Total Employees | Card | `[Total Employees]` |
| 2 | Employees Who Left | Card | `[Employees Left]` |
| 3 | Attrition Rate | Card | `[Attrition Rate]` (format 0.0%) |
| 4 | Average Employee Age | Card | `[Average Age]` (1 decimal) |
| 5 | Department-wise Attrition | Clustered column | X `Department`, Y `[Attrition Rate]`; add *constant line* = `[Company Attrition Rate]` |
| 6 | Gender-wise Attrition | Donut | Legend `Gender`, Values `[Employees Left]` |
| 7 | Job Role-wise Attrition | Clustered bar (sorted desc) | Y `JobRole`, X `[Attrition Rate]` |

### Page 2 – Attrition Drivers
| # | Requirement | Visual | Fields |
|---|---|---|---|
| 8 | Salary-wise Attrition | Column | X `SalaryBand`, Y `[Attrition Rate]` |
| 9 | Job Satisfaction Analysis | Column + Matrix | X `JobSatisfactionLevel`, Y `[Attrition Rate]`; matrix rows `JobSatisfactionLevel` × cols `OverTime`, values `[Attrition Rate]` (heat-map conditional format) |
| 10 | Overtime Impact | Column + 3 cards | X `OverTime`, Y `[Attrition Rate]`; cards `[Overtime Impact (x)]` etc. |
| 11 | Employee Experience Analysis | Column (+ line) | X `ExperienceBand`, Y `[Attrition Rate]`; optional second chart on `TenureBand` |
| – | Extras | Column | `EducationLevel`, `AgeGroup` vs `[Attrition Rate]` |

### Page 3 – Predicted Attrition (ML)
| # | Requirement | Visual | Fields |
|---|---|---|---|
| 12 | Predicted Attrition Analysis | Cards | `[Predicted Leavers]`, `[High Risk Employees]`, `[Model Recall]`, `[Model Precision]` |
| | | Column | X `Risk_Level`, Y `[Total Employees]` (colour: Low green / Medium amber / High red) |
| | | Column | X `Risk_Level`, Y `[Attrition Rate]` – shows the risk tiers are meaningful |
| | | Clustered column | X `Department`, Y `[Employees Left]` and `[Predicted Leavers]` |
| | | Table (watch-list) | `EmployeeID, Department, JobRole, Age, MonthlyIncome, OverTime, Attrition_Probability`; filter **Risk_Level = High**, Top N by probability; data bars on probability |

## 4. Formatting tips
- Conditional-format column colours with the `[Attrition Colour]` measure (*Format → Columns → Colors → fx → Field value*).
- Turn on **Data labels**; hide gridlines and Y-axes on small charts for a clean look.
- Add **Tooltips pages** (Employees, Employees Left) and **Drill-through** from Department → JobRole.
- Add bookmarks + buttons (Reset filters) and a *Navigation* page-navigator visual.
- Publish: *Home → Publish* → Power BI Service; pin to a dashboard; export a PDF for your portfolio.

## 5. Reference numbers (use to validate your build)
Total 1,470 · Left 227 · Attrition 15.4 % · Avg age 36.9 · Overtime 26.0 % vs 11.3 % · High-risk employees 141.
If your cards match, the model and measures are wired correctly.
