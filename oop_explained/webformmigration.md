# ASP.NET Web Forms → Angular / React + Web API Migration Plan

## Determinism & Consistency Rules

> **CRITICAL — READ FIRST:** This migration plan must produce **identical output** every time it is executed against the same source and destination projects. Follow these rules to eliminate variation:

### Decision Resolution Order

When this document offers multiple alternatives (separated by `/`, `or`, or listed in a table), **never pick randomly**. Always resolve using this strict priority:

1. **Use what is already installed in the destination project.** Scan `package.json` (frontend) and `.csproj` (Web API) for installed packages. If a package is already present, use it — no exceptions.
2. **If nothing is installed, use the first option listed** in this document. The first option in every list, table cell, or slash-separated pair is the **default**. Only use a later option if the first is explicitly incompatible with the destination project's framework version.
3. **Never introduce a new library** that is not already installed in the destination project and not listed as the first option in this document.

### Processing Order

- **Phase execution:** Always execute Phase 1 → Phase 2 → Phase 3 → Phase 5 in strict order. Phase 4 is a reference table consulted during Phase 3 only.
- **Page processing order:** Process pages in this order: **Auth/Login pages first** (login, registration, account management — needed before other features), then remaining pages in **alphabetical order by page name** (e.g., `Dashboard.aspx` before `Orders.aspx`), then complex feature pages last (pages with heavy UpdatePanel AJAX, file upload, real-time features). Within each page, process event handlers in the order they appear in the code-behind file, top to bottom.
- **View processing order:** For each logical feature (page group), process pages in this fixed order: List/Grid page → Details page → Create/Add page → Edit page → Delete page → any remaining pages alphabetically.
- **Service/DTO creation order:** Create services and DTOs in the same order as their associated pages are processed.

### Naming Conventions (deterministic)

All generated file and symbol names must follow these exact rules — no creative renaming:

> **[ANGULAR ONLY]:**
> - Component: `{source-page-name}.component.ts` (kebab-case) — e.g., `student-list.component.ts`, `student-detail.component.ts`
> - Service: `{feature-name}.service.ts` — e.g., `student.service.ts`
> - Model/Interface: `{dto-name}.model.ts` — e.g., `student.model.ts`
> - Module (if NgModule): `{feature-name}.module.ts` — e.g., `student.module.ts`
> - Guard: `{feature-name}.guard.ts` — e.g., `auth.guard.ts`
> - Interceptor: `{purpose}.interceptor.ts` — e.g., `auth.interceptor.ts`, `error.interceptor.ts`
> - Folder structure: `src/app/{feature-name}/` — one folder per logical feature group (pages that share the same data domain)

> **[REACT ONLY]:**
> - Page component: `{SourcePageName}Page.tsx` (PascalCase) — e.g., `StudentListPage.tsx`, `StudentDetailPage.tsx`
> - Component: `{SourcePageName}.tsx` — e.g., `StudentForm.tsx`
> - Hook: `use{Feature}.ts` — e.g., `useStudents.ts`
> - Service: `{feature}Service.ts` (default). Use `{feature}Api.ts` only if the destination project already uses the `*Api.ts` naming pattern.
> - Model/Interface: `{dto-name}.types.ts` — e.g., `student.types.ts`
> - Folder structure: `src/pages/{feature-name}/` for pages, `src/components/{feature-name}/` for shared components — one folder per logical feature group

> **Web API (both frameworks):**
> - Controller: `{FeatureName}Controller.cs` — Group related page code-behind methods into a single API controller per feature domain
> - DTO: Follow destination project's existing naming convention. Scan for existing patterns: `*Dto`, `*Request`/`*Response`, `*Model`, or no suffix. If destination has no established convention, default to `{EntityName}Dto.cs`.
> - Service interface: `I{ServiceName}.cs`
> - Service implementation: `{ServiceName}.cs`
> - AutoMapper profile: `{Feature}MappingProfile.cs`

**Override:** If the destination project already has established naming conventions that differ from the above, use the destination's conventions instead. Document which convention is followed in the inventory summary.

### Code Style Determinism

- **Do not** add comments like `// TODO`, `// FIXME`, or explanatory comments to generated code unless the source code had them.
- **Do not** reorder properties, methods, or fields. Preserve the source code's ordering.
- **Do not** rename variables or method parameters. Keep original names; only change the type/signature where required by the framework.
- **Do not** refactor, optimize, or "improve" source logic. Migrate it verbatim.
- **String literals:** Preserve all string values (error messages, labels, button text) exactly as they appear in the source — character for character, including casing and punctuation.

---

## Session Resilience & Checkpoint Resume

> **CRITICAL:** This migration may span multiple sessions. The AI session may time out, the connection may break, or the user may need to pause and resume later. The migration **must not restart from scratch** when this happens. Follow these rules to ensure continuity.

### Migration Progress Tracker

At the start of every migration (or resume), create and maintain a progress tracker file in the **destination frontend project root** named `MIGRATION_PROGRESS.md`. This file is the single source of truth for what has been completed.

**Create this file immediately after Phase 1 inventory is confirmed by the user.** Structure it exactly as follows:

```markdown
# Migration Progress Tracker
<!-- AUTO-GENERATED — do not edit manually. Updated by migration agent after each step. -->

## Session Info
- Framework: [Angular/React]
- Source Web Forms: [path]
- Dest Frontend: [path]
- Dest Web API: [path]
- Kendo: [yes/no, version]
- Started: [date]
- Last Updated: [date-time]

## Phase Status
- [x] Phase 1: Source Analysis — COMPLETED
- [ ] Phase 2: Backend Migration — [NOT STARTED / IN PROGRESS / COMPLETED]
- [ ] Phase 3: Frontend Migration — [NOT STARTED / IN PROGRESS / COMPLETED]
- [ ] Phase 5: Verification — [NOT STARTED / IN PROGRESS / COMPLETED]

## One-Time Setup Status
- [ ] Environment config files set
- [ ] Auth pages migrated
- [ ] Auth interceptor created
- [ ] Route guard created
- [ ] Error pages created
- [ ] SignalR service/hook created (if applicable)
- [ ] Localization setup (if applicable)
- [ ] Bing Maps one-time setup done (if applicable)
- [ ] CSS/assets base migration done

## Page Migration Status
<!-- One row per page (or logical feature group), alphabetical order. Update status after EACH page completes. -->
<!-- Column mapping to Phase 5 per-page checklist:
  Backend API = API Controller + endpoints for this page's postbacks/data operations
  Backend Data = Entities, EF configs, seed data, stored procedures migration for this page's domain
  Backend Services = Services + Interfaces + DTOs + AutoMapper profile + DI registration + appsettings
  Backend Validations = All server-side validations + localized messages
  Frontend Components = TS interfaces/models + service/hook + page components + routing
  Frontend Validations = Client-side validations + ProblemDetails inline display
  Frontend Features = File upload, UpdatePanel replacement, localization, Kendo controls, CSS (if applicable)
-->
| Page / Feature | Backend API | Backend Data | Backend Services | Backend Validations | Frontend Components | Frontend Validations | Frontend Features | Status |
|---|---|---|---|---|---|---|---|---|
| Login.aspx | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | NOT STARTED |
| Dashboard.aspx | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | NOT STARTED |
| ... | | | | | | | | |

## Current Position
- **Currently working on:** [Phase X, PageName, Step Y]
- **Next step:** [description of what to do next]
- **Last completed file:** [path of last file created/modified]
```

### Checkpoint Rules

1. **Update `MIGRATION_PROGRESS.md` after every completed unit of work.** A unit of work is:
   - Completing a phase
   - Completing one-time setup items
   - Completing a page's backend migration (all backend checklist items for that page)
   - Completing a page's frontend migration (all frontend checklist items for that page)
   - Completing any standalone section (CSS migration, error pages, etc.)

2. **Always update the "Current Position" section** before starting any new unit of work, so that if the session breaks mid-work, the resume knows exactly where to pick up.

3. **Mark checkboxes as `[x]`** in the tracker as each item completes. Never uncheck a completed item.

### How to Resume After a Break

> **USER INSTRUCTION:** If the migration was interrupted by a session timeout, paste this entire `webformmigration.md` prompt into the new session and add the line: **"Resume the migration — check MIGRATION_PROGRESS.md for the checkpoint."** The AI will then follow the resume protocol below.

When a session starts (or is restarted after a timeout/break), **before doing anything else**, follow these steps:

1. **Check if `MIGRATION_PROGRESS.md` exists** in the destination frontend project root.

2. **If it does NOT exist** — this is a fresh migration. Proceed normally from the "Workspace Modification Permission" section.

3. **If it DOES exist** — this is a **resume**. Do the following:
   a. Read `MIGRATION_PROGRESS.md` completely.
   b. Read the "Session Info" section to restore all project paths, framework choice, and Kendo settings — **do NOT re-ask the user for these**.
   c. Read "Phase Status" to determine which phase is current.
   d. Read "Page Migration Status" to determine which pages are already done.
   e. Read "Current Position" to determine exactly where to resume.
   f. **Verify the last completed work** — check that the files listed as "Last completed file" actually exist and are valid. If the last unit was interrupted mid-way (file exists but is incomplete), redo only that unit.
   g. **Print a resume summary** to the user:
      ```
      Resuming migration from checkpoint:
      - Phase: [X]
      - Last completed: [page/step]
      - Next: [page/step]
      - Pages done: [N of M]
      ```
   h. **Ask the user:** "Resume from this checkpoint? (yes / restart from scratch)"
   i. If **yes** — continue from the "Next step" recorded in the tracker. Do not repeat completed work.
   j. If **restart** — delete `MIGRATION_PROGRESS.md` and start fresh from "Workspace Modification Permission".

### Preventing Session Timeout

To minimize the risk of session breaks during large migrations:

1. **Work in small atomic units.** Complete ONE page's backend migration fully, update the tracker, then proceed to the next. Do not batch multiple pages.

2. **Do not generate large code blocks without saving.** After generating each file, write it to disk immediately. Do not accumulate multiple files in memory before writing.

3. **Prefer multiple small file writes over one massive output.** If a page has 4 components, write each component file individually rather than generating all 4 at once.

4. **After every 3 pages completed**, print a brief status update to the user:
   ```
   Progress: [N/M] pages migrated. Checkpoint saved.
   ```

5. **If the migration has more than 10 pages**, process them in batches of 5. After each batch:
   - Update `MIGRATION_PROGRESS.md`
   - Print progress summary
   - Continue to next batch without pausing (unless user interrupts)

### Recovery from Partial File Writes

If a session breaks while a file was being written:
- On resume, check the "Last completed file" from the tracker.
- If the file exists but appears truncated (missing closing braces, incomplete class, syntax errors), **delete and regenerate** that single file.
- If the file does not exist, generate it from scratch.
- Do NOT re-generate files that were fully completed in previous sessions — check the tracker.

---

## Workspace Modification Permission

Before starting any migration work, ask the user:

**"This migration will create, modify, and reorganize files across your frontend and Web API projects. Do you grant permission to modify your workspace for the entire migration operation? (yes/no)"**

- If **yes** — Proceed with all file creation, modification, and reorganization steps throughout the entire migration without asking for permission again at each individual step.
- If **no** — Ask for explicit confirmation before each file creation, modification, or deletion during the migration process.

Do not proceed with any migration phases until this permission is granted or denied.

---

## Frontend Framework Selection

Ask the user:

**"Which frontend framework are you migrating to? (Angular / React)"**

- Store the answer as `[SELECTED_FRAMEWORK]` — all `[ANGULAR ONLY]` or `[REACT ONLY]` sections below apply based on this choice.
- Skip all sections marked `[ANGULAR ONLY]` if React was selected.
- Skip all sections marked `[REACT ONLY]` if Angular was selected.
- Sections with no tag apply to both frameworks.

Do not proceed until a valid choice (Angular or React) is made.

---

## Project Paths

Ask the user for each path one at a time. Do not proceed to the next question until the current path is provided and validated:

1. First, ask: **"Please provide the full path to the Source ASP.NET Web Forms project:"** — Wait for response, validate the path exists and contains a `.csproj` file (or `.vbproj` for VB.NET Web Forms). Verify it is a Web Forms project by checking for `*.aspx` files, `Global.asax`, or `Web.config` with `<system.web>` configuration.

2. Then ask for the destination frontend project path based on the selected framework:

   > **[ANGULAR ONLY]** — "Please provide the full path to the Destination Angular project:" — Validate the path exists and contains a `package.json` and `angular.json`.

   > **[REACT ONLY]** — "Please provide the full path to the Destination React project:" — Validate the path exists and contains a `package.json` and either `vite.config.ts`, `vite.config.js`, or `react-scripts` in dependencies.

3. Then ask: **"Please provide the full path to the Destination C# Web API project:"** — Wait for response, validate the path exists and contains a `.csproj` file.

Do not proceed with any migration until all three paths are collected and validated.

4. Then ask: **"Does the source Web Forms application use Telerik/Kendo controls? (yes/no):"**

   - If **yes** — ask: **"Which Telerik product is used? (Telerik UI for ASP.NET AJAX / Telerik RadControls / Kendo UI for jQuery — check `Web.config` for `Telerik.Web.UI` or page `<%@ Register %>` directives):"**
     - Use the provided information as a reference for feature parity when selecting equivalent Kendo components in the destination project.

   > **[ANGULAR ONLY] — If yes:**
   > - Check whether `@progress/kendo-angular-*` packages already exist in the destination project's `package.json`.
   > - **If already installed** — use the installed version as-is. Do **not** run any install commands. Skip the version question below.
   > - **If not installed** — ask: **"Which version of Kendo Angular do you want to install in the destination project? (e.g., 16.x, 17.x — or press Enter to install latest):"**
   >   - Use the specified version when installing packages (e.g., `@progress/kendo-angular-grid@16.x`). If no version is given, install the latest compatible with the project's Angular version.
   >   - Install only the specific Kendo Angular packages needed for the controls being migrated (e.g., `@progress/kendo-angular-grid`, `@progress/kendo-angular-dropdowns`). Do not install the entire Kendo suite.
   > - Note: This is a one-time setup step only. Continue with Phase 1 → 2 → 3 in order. Phase 4's Kendo Angular control mapping table will be referenced **during Phase 3** whenever a Telerik/Kendo control is encountered — do not skip ahead to Phase 4.

   > **[ANGULAR ONLY] — If no:** Skip Phase 4 and use standard HTML/Angular Material controls based on what's installed in the destination Angular project.

   > **[REACT ONLY] — If yes:**
   > - Check whether `@progress/kendo-react-*` packages already exist in the destination project's `package.json`.
   > - **If already installed** — use the installed version as-is. Do **not** run any install commands. Skip the version question below.
   > - **If not installed** — ask: **"Which version of Kendo React do you want to install in the destination project? (e.g., 8.x, 9.x — or press Enter to install latest):"**
   >   - Use the specified version when installing packages (e.g., `@progress/kendo-react-grid@8.x`). If no version is given, install the latest compatible with the project's React version.
   >   - Install only the specific Kendo React packages needed for the controls being migrated (e.g., `@progress/kendo-react-grid`, `@progress/kendo-react-dropdowns`). Do not install the entire Kendo suite.
   > - Note: This is a one-time setup step only. Continue with Phase 1 → 2 → 3 in order. Phase 4's Kendo React control mapping table will be referenced **during Phase 3** whenever a Telerik/Kendo control is encountered — do not skip ahead to Phase 4.

   > **[REACT ONLY] — If no:** Skip Phase 4 and use standard HTML/React controls (Material UI, Ant Design, etc.) based on what's installed in the destination React project.

5. Then ask: **"What is the source project's .NET Framework version? (e.g., 4.5, 4.6.1, 4.7.2, 4.8):"** — This determines the data access patterns, authentication model, and assembly references to expect.

6. Then ask: **"What is the source project's language? (C# / VB.NET):"** — If VB.NET, all code-behind logic must be translated to C# during migration to the Web API project.

---

## Overview

Migrate monolithic ASP.NET Web Forms app into: **[SELECTED_FRAMEWORK]** (existing project, UI) + **C# Web API** (existing project, backend).

> **Web Forms Migration Context:** ASP.NET Web Forms applications use a fundamentally different architecture from modern SPA frameworks. They rely on server-rendered pages with postback-driven state management (ViewState), server controls with event handlers, and a page lifecycle model. This migration must decompose the tightly-coupled page+code-behind into a clean API backend and SPA frontend.

> **Before starting:** Verify the following are already configured in the destination projects. If any are missing, resolve them before generating migration code:
> - **Web API:** JWT Bearer auth middleware, CORS policy that allows the frontend origin, Swagger/OpenAPI (optional but recommended)
> - **Frontend:** HTTP client setup — Angular: `HttpClientModule` (or `provideHttpClient()` for standalone); React: `axios` if installed, otherwise native `fetch`
> - **Auth interceptor:** Will be created during Phase 3 Auth UI migration if not already present in the destination project

### Pre-Migration: Analyze Destination Projects First

Before generating any code, **analyze both destination projects** to understand:

---

> **[ANGULAR ONLY] — Angular Project Analysis:**
> - Existing folder structure, module organization (standalone vs NgModule), routing setup
> - Installed packages (`package.json`) — identify Kendo Angular, Angular Material, Bootstrap, ngx-toastr, etc.
> - Existing shared/core modules, interceptors, guards, services already in place
> - Coding conventions — naming patterns, file organization, state management approach
> - Angular version and syntax style (e.g., control flow `@if`/`@for` vs `*ngIf`/`*ngFor`)
> - Existing environment config files and API URL setup

---

> **[REACT ONLY] — React Project Analysis:**
> - Existing folder structure, component organization (pages, components, hooks, etc.)
> - Installed packages (`package.json`) — identify Kendo React, MUI, Ant Design, React Query, Zustand, Redux, axios, react-hook-form, yup/zod, etc.
> - Existing shared components, custom hooks, context providers, route guards already in place
> - Coding conventions — naming patterns, TypeScript usage, file organization, state management approach
> - React version and syntax style (class vs functional components; hooks usage)
> - Existing environment config files (`VITE_*` / `REACT_APP_*`) and API base URL setup
> - Bundler in use: Vite, Create React App (CRA), or custom webpack

---

**Web API Project:**
- Existing folder structure, namespace conventions, project layers
- Installed packages (`.csproj`) — identify EF Core, AutoMapper, FluentValidation, MediatR, etc.
- Existing middleware pipeline, DI registrations in `Program.cs`/`Startup.cs`
- Existing base classes, shared DTOs, response wrappers, error handling patterns
- Auth configuration already in place (JWT, Identity, policies)
- Existing DbContext, entity configurations, migration history

**All generated code must follow the destination project's existing patterns, conventions, and folder structure. Do not impose a new structure — adapt to what is already there.**

### Migration Must Include

- **All server-side validations (STRICT — migrate every rule)** — ASP.NET validator controls (`RequiredFieldValidator`, `RegularExpressionValidator`, `RangeValidator`, `CompareValidator`, `CustomValidator`), code-behind validation logic (manual checks in event handlers, `Page.IsValid`, `Validate()` calls), custom `BaseValidator` subclasses, business rule validations in data layer → migrate **all** to API DTOs with identical rules (server-side using data annotations and/or FluentValidation). Do not skip, simplify, or weaken any validation rule. Every field constraint, conditional rule, cross-field comparison, and custom error message must be preserved exactly.
- **All client-side validations (STRICT — migrate every rule to the frontend):**
  > **CRITICAL:** Every validation that executes in the browser in the source Web Forms app must have a corresponding client-side validator in the destination frontend. This includes: ASP.NET validator controls with `EnableClientScript="true"` (default), `CustomValidator` with `ClientValidationFunction`, custom JavaScript validation in `<script>` blocks or external `.js` files, inline `onchange`/`onblur` validation handlers, and any validation logic attached via `ScriptManager` or `RegisterClientScriptBlock`. **No validation may exist only on the server — if it was client-side in Web Forms, it must remain client-side in the destination.**

  > **[ANGULAR ONLY]** Migrate every client-side validation rule to Angular Reactive Forms:
  > - `RequiredFieldValidator` → `Validators.required`
  > - `RegularExpressionValidator` → `Validators.pattern()` (use the exact same regex from `ValidationExpression`)
  > - `RangeValidator` → `Validators.min()` / `Validators.max()`
  > - `CompareValidator` (DataTypeCheck) → `Validators.pattern()` for type format
  > - `CompareValidator` (Equal/NotEqual/GreaterThan) → custom cross-field `ValidatorFn`
  > - `StringLengthValidator` / `MaxLength` property → `Validators.minLength()` / `Validators.maxLength()`
  > - `CustomValidator` with `ClientValidationFunction` → custom `ValidatorFn` with the same logic
  > - `CustomValidator` with server-side `ServerValidate` only → custom `AsyncValidatorFn` calling the equivalent API endpoint
  > - All custom error messages (`ErrorMessage`, `Text` properties) → `{ errorKey: 'Exact same error message' }` in the validator or displayed via `<mat-error>` / custom error component
  > - `ValidationSummary` control → form-level error summary component with matching display mode (`BulletList`, `List`, `SingleParagraph`)
  > - Conditional validations (validators with `Enabled` set dynamically in code-behind) → `ValidatorFn` that checks the condition at runtime

  > **[REACT ONLY]** Migrate every client-side validation rule to `react-hook-form` + `yup` schema (default; use `zod` only if `zod` is already installed in the destination and `yup` is not):
  > - `RequiredFieldValidator` → `yup.string().required('message')` (if using zod: `z.string().min(1, 'message')`)
  > - `RegularExpressionValidator` → `.matches(pattern, message)` using exact regex from `ValidationExpression` (if using zod: `z.string().regex()`)
  > - `RangeValidator` → `.min()` / `.max()` with original messages
  > - `CompareValidator` (DataTypeCheck) → `.matches()` for type format
  > - `CompareValidator` (Equal/NotEqual/GreaterThan) → `.oneOf([yup.ref('field')])` or `.test()` for cross-field comparison (if using zod: `zod.refine()`)
  > - `StringLengthValidator` / `MaxLength` property → `.min()` / `.max()` with original messages
  > - `CustomValidator` with `ClientValidationFunction` → custom `yup.test()` with the same logic (if using zod: `zod.refine()`)
  > - `CustomValidator` with server-side `ServerValidate` only → custom async `yup.test()` calling the API endpoint (if using zod: `zod.refine()`)
  > - All custom error messages → preserved exactly in the schema `.required('Same message')` / `.min(n, 'Same message')`
  > - `ValidationSummary` control → form-level error summary component
  > - Conditional validations → `.when()` in yup (if using zod: `.refine()` with conditional logic)
- **All data access logic** — ADO.NET (`SqlConnection`, `SqlCommand`, `SqlDataReader`, `SqlDataAdapter`, `DataSet`, `DataTable`), LINQ to SQL, Entity Framework 6, stored procedures, inline SQL → migrate to EF Core in the Web API project. Preserve all query logic, filtering, sorting, and paging.
- **All business logic from code-behind** — `Page_Load`, button click handlers (`btn_Click`), `SelectedIndexChanged`, `RowCommand`, `RowDataBound`, timer tick handlers → extract into Web API services and controllers
- **Custom HTTP Modules** — Authentication modules, URL rewriting, logging, compression → Web API middleware pipeline
- **Custom HTTP Handlers** (`.ashx`) — File download handlers, image handlers, API-like handlers → Web API controllers
- **Global.asax event handlers** — `Application_Start`, `Application_Error`, `Session_Start`, `Application_BeginRequest` → Web API `Program.cs` configuration and middleware
- **Custom server controls** (`.ascx` code-behind, custom `WebControl` / `CompositeControl` subclasses):
  > **[ANGULAR ONLY]** → Angular components, directives, or pipes
  > **[REACT ONLY]** → React components, custom hooks, or utility functions
- **Custom validation controls** — `BaseValidator` subclasses → API: custom validation attributes on DTOs + frontend: custom validator functions
- **Business rule validations** — Service-layer validations, data layer validations → preserve in Web API services, surface errors via `ProblemDetails` to the frontend
- **All database schemas** — Migrate data access layer (ADO.NET, DataSets, EF6, stored procedures) to EF Core in the destination Web API project
- **SignalR** (if present, typically via `Microsoft.AspNet.SignalR`) — Migrate hubs to ASP.NET Core SignalR in Web API; create a frontend service/hook to connect via `@microsoft/signalr`
- **Background jobs** (if present) — Migrate timer-based background tasks, `Thread`/`ThreadPool` usage, or third-party schedulers into Web API `IHostedService` / `BackgroundService`
- **Web Services** (`.asmx` SOAP/XML services, if present) — Migrate to REST API controllers in the Web API project
- **WCF service references** (if present) — Replace with HTTP API calls to equivalent REST endpoints

---

## Phase 1: Analyze Source Web Forms App

Inventory all: Pages (`.aspx` + code-behind), Master Pages (`.master`), User Controls (`.ascx`), Data objects / business entities, Data access layer (ADO.NET/DataSets/EF6/stored procedures), Static assets, Third-party controls (Telerik, Kendo, ComponentArt, DevExpress, etc.), HTTP Modules/Handlers, Custom Validations, Global.asax handlers, Web Services (`.asmx`), WCF references, Bing Maps usage.

**Before proceeding to Phase 2, produce an inventory summary** listing:
- All pages (`.aspx`) and their postback event count (button clicks, grid commands, dropdown changes, etc.)
- All pages grouped by logical feature (e.g., Student management: `StudentList.aspx`, `StudentEdit.aspx`, `StudentDetails.aspx`)
- All Master Pages (`.master`) and which pages use each one
- All User Controls (`.ascx`) and where they are referenced (which `.aspx` pages)
- All custom server controls (classes inheriting `WebControl`, `CompositeControl`, `BaseValidator`)
- All data access classes and patterns — ADO.NET direct queries, typed DataSets (`.xsd`), Entity Framework 6 models, LINQ to SQL classes, Repository classes
- All stored procedures called from code-behind (list proc name + which page calls it)
- All third-party controls detected (Telerik RadGrid, RadComboBox, etc.)
- All client-side validations — list every form with its ASP.NET validator controls (`RequiredFieldValidator`, `RegularExpressionValidator`, `RangeValidator`, `CompareValidator`, `CustomValidator`), their `ErrorMessage`/`Text` properties, `ValidationGroup` assignments, and any `CustomValidator` `ClientValidationFunction` JavaScript
- All server-side validations — `CustomValidator` `ServerValidate` handlers, manual `Page.IsValid` checks, code-behind business rule checks
- All `ValidationSummary` controls and their `DisplayMode` / `ShowMessageBox` / `ShowSummary` settings
- All Web Services (`.asmx`) and their `[WebMethod]` signatures
- All WCF service references and their operation contracts
- All HTTP Handlers (`.ashx`) and their purpose
- All HTTP Modules registered in `Web.config` `<system.webServer><modules>`
- All `Global.asax` event handlers and what they do
- All file upload controls (`<asp:FileUpload>`, `RadAsyncUpload`, etc.)
- All custom error pages configured in `Web.config` `<customErrors>`
- Localization/i18n usage — `.resx` resource files, `GetLocalResourceObject()`, `GetGlobalResourceObject()`, `meta:resourcekey` attributes, localized validator messages (if any)
- `Web.config` analysis — connection strings, app settings, authentication mode, session state configuration, custom configuration sections
- All JavaScript files in the project — `<script>` references in pages/master pages, `ScriptManager` `ScriptReference` entries, `RegisterClientScriptBlock`/`RegisterStartupScript` calls, external `.js` files
- All `UpdatePanel` usages — list each page and what content is inside the UpdatePanel(s), what triggers them, and the async postback behavior
- `ScriptManager` / `ToolkitScriptManager` usage and registered scripts/services
- All `Page` directives (`<%@ Page %>`) — note `MasterPageFile`, `EnableViewState`, `ValidateRequest`, `Culture`/`UICulture` settings

Present this summary to the user and wait for confirmation before beginning Phase 2.

**After user confirms the inventory:** Create `MIGRATION_PROGRESS.md` in the destination frontend project root (see **Session Resilience & Checkpoint Resume** section for exact format). Populate the "Session Info", mark Phase 1 as `[x] COMPLETED`, and populate the "Page Migration Status" table with all pages/features from the inventory in alphabetical order, all marked `NOT STARTED`.

**Library Mapping:**

> **[ANGULAR ONLY]**

> Resolution: Use the **first** package in the "Angular Equivalent" column. If it is not installed and not compatible, try the next. See **Determinism & Consistency Rules** above.

| Web Forms Control / Library | Angular Equivalent (priority order — use first match) |
|---|---|
| Telerik RadControls / Kendo AJAX | `@progress/kendo-angular-*` |
| Bootstrap (if used) | 1. `@ng-bootstrap/ng-bootstrap` → 2. `ngx-bootstrap` |
| ASP.NET Validator Controls | Angular Reactive Forms (built-in, no package needed) |
| `GridView` / `RadGrid` / DataGrid | 1. `@progress/kendo-angular-grid` (if Kendo confirmed) → 2. Angular Material Table |
| `DropDownList` / `RadComboBox` | 1. `@progress/kendo-angular-dropdowns` (if Kendo confirmed) → 2. Angular Material `<mat-select>` |
| Charting controls (RadChart, etc.) | 1. `@progress/kendo-angular-charts` (if Kendo confirmed) → 2. `ngx-charts` |
| `ScriptManager` alerts / custom popups | 1. `ngx-toastr` → 2. `sweetalert2` |
| Bing Maps | **STRICT — must use Bing Maps V8 SDK directly.** Install `bingmaps` types (`npm install bingmaps`). Load the Bing Maps script (`https://www.bing.com/api/maps/mapcontrol`) in `index.html` or dynamically via a service. Read the API key from `environment.ts` (placeholder `bingMapsKey: ''` — user will add the actual key to `appsettings.json` post-migration). Use `Microsoft.Maps.Map` API in `AfterViewInit` with `ElementRef`. Do not substitute with Google Maps, Leaflet, or any other map provider. |
| `AjaxControlToolkit` controls | Map each control individually: `CalendarExtender` → `<kendo-datepicker>` / `<mat-datepicker>`, `AutoCompleteExtender` → `<kendo-autocomplete>` / `<mat-autocomplete>`, `ModalPopupExtender` → `<kendo-dialog>` / `<mat-dialog>`, `TabContainer` → `<kendo-tabstrip>` / `<mat-tab-group>`, `CollapsiblePanelExtender` → `<kendo-expansionpanel>` / `<mat-expansion-panel>`, `FilteredTextBoxExtender` → `Validators.pattern()` on `<input>`, `MaskedEditExtender` → `<kendo-maskedtextbox>` |

---

> **[REACT ONLY]**

> Resolution: Use the **first** package in the "React Equivalent" column. If it is not installed and not compatible, try the next. See **Determinism & Consistency Rules** above.

| Web Forms Control / Library | React Equivalent (priority order — use first match) |
|---|---|
| Telerik RadControls / Kendo AJAX | `@progress/kendo-react-*` |
| Bootstrap (if used) | 1. `react-bootstrap` → 2. `reactstrap` |
| ASP.NET Validator Controls | `react-hook-form` + `yup` (default). Use `zod` only if `zod` is already installed and `yup` is not. |
| `GridView` / `RadGrid` / DataGrid | 1. `@progress/kendo-react-grid` (if Kendo confirmed) → 2. MUI DataGrid → 3. `@tanstack/react-table` |
| `DropDownList` / `RadComboBox` | 1. `react-select` → 2. `@progress/kendo-react-dropdowns` (if Kendo confirmed) |
| Charting controls (RadChart, etc.) | 1. `@progress/kendo-react-charts` (if Kendo confirmed) → 2. `recharts` → 3. `@nivo/core` |
| `ScriptManager` alerts / custom popups | 1. `react-toastify` → 2. `sweetalert2` |
| Bing Maps | **STRICT — must use Bing Maps V8 SDK directly.** Install `bingmaps` types (`npm install bingmaps`). Load the Bing Maps script (`https://www.bing.com/api/maps/mapcontrol`) dynamically in a `useEffect` hook. Read the API key from environment config (`VITE_BINGMAPS_KEY` or `REACT_APP_BINGMAPS_KEY` — user will add the actual key post-migration; use a placeholder during migration). Use `Microsoft.Maps.Map` on a `useRef<HTMLDivElement>` container. Do not substitute with Google Maps, Leaflet, or any other map provider. |
| `AjaxControlToolkit` controls | Map each control individually: `CalendarExtender` → `<DatePicker>` from Kendo / date-fns picker, `AutoCompleteExtender` → `react-select` Async, `ModalPopupExtender` → `<Dialog>` from Kendo / MUI `<Dialog>`, `TabContainer` → `<TabStrip>` from Kendo / MUI `<Tabs>`, `CollapsiblePanelExtender` → `<ExpansionPanel>` from Kendo / MUI `<Accordion>`, `FilteredTextBoxExtender` → input with `pattern` + `yup.matches()`, `MaskedEditExtender` → `react-input-mask` or Kendo `<MaskedTextBox>` |

---

## Phase 2: Backend — Web Forms Code-Behind → Web API

*(Applies to both Angular and React — no framework-specific differences)*

### Web Forms → Web API Conversion Strategy

> **Key Concept:** In Web Forms, business logic, data access, and UI rendering are tightly coupled in code-behind files (`.aspx.cs`/`.aspx.vb`). The migration must **decompose** this into three layers:
> 1. **API Controller** — Handles HTTP requests, delegates to services, returns JSON
> 2. **Service Layer** — Contains all business logic extracted from code-behind event handlers
> 3. **Data Layer** — EF Core replaces ADO.NET/DataSets/EF6/stored procedures

### Code-Behind Extraction Rules

- **`Page_Load` with `!IsPostBack`** → API GET endpoint(s) that return the initial data for the page
- **`Page_Load` with `IsPostBack`** → Usually no direct equivalent (postback state is eliminated); any logic that ran on every postback should become server-side validation or middleware
- **Button click handlers** (`btnSave_Click`, `btnDelete_Click`, `btnSearch_Click`) → API POST/PUT/DELETE endpoints
- **Grid event handlers** (`GridView_RowCommand`, `GridView_RowDataBound`, `GridView_PageIndexChanging`, `GridView_Sorting`) → API GET endpoint with query parameters for paging/sorting/filtering; `RowCommand` actions (Edit, Delete, Select) → individual API endpoints
- **DropDownList `SelectedIndexChanged`** (with `AutoPostBack="true"`) → Frontend `onChange` handler calling an API endpoint to fetch dependent data (cascading dropdowns)
- **Timer `Tick` handlers** → Frontend polling via `setInterval` / RxJS `interval` calling an API endpoint, or replace with SignalR real-time push
- **`UpdatePanel` async postbacks** → Replace entirely with proper API calls from the frontend. The `UpdatePanel` pattern is eliminated — all data fetching becomes explicit HTTP requests.
- **`Response.Redirect` / `Server.Transfer`** → Return appropriate HTTP status codes; frontend handles routing
- **`Session["key"]` reads/writes** → API-side: use JWT claims, in-memory cache, or distributed cache. Frontend-side: store in component state, service, or state management store.
- **`ViewState` usage** → Eliminated entirely. All state management moves to the frontend (component state, form state, URL parameters) or API (server-side caching if needed).
- **`Application["key"]`** → Singleton service in DI or distributed cache
- **`Cache["key"]` / `HttpRuntime.Cache`** → `IMemoryCache` or `IDistributedCache` in Web API DI
- **`Request.QueryString` / `Request.Form`** → `[FromQuery]` / `[FromBody]` parameters on API controller actions
- **`Request.Files` / `FileUpload.PostedFile`** → `[FromForm] IFormFile` on API controller actions
- **`ScriptManager.RegisterStartupScript` / `RegisterClientScriptBlock`** → Eliminated; dynamic UI updates happen via frontend framework binding

### Per-Page Steps

For each `.aspx` page and its code-behind:

1. **Analyze the page's data flow** — Identify all data sources (SQL queries, stored procedures, business objects), all user interactions (buttons, grid commands, dropdown changes), and all data transformations in the code-behind.
2. **Design API endpoints** — Map each distinct data operation to a REST endpoint. One page may produce multiple API endpoints. Group related endpoints into a single API controller per feature domain.
3. Create API controller following **destination project's existing controller conventions** — use `[ApiController]`, `[Route("api/[controller]")]`, proper HTTP verbs
4. **Extract business logic into service classes** — Move all non-UI logic from code-behind into service interfaces/implementations. Register in DI.
5. Create DTOs following destination's existing DTO patterns; add AutoMapper profiles to existing profile structure
6. **Migrate all validations** — Map every ASP.NET validator control and code-behind validation check to data annotations / FluentValidation rules on DTOs
7. Migrate custom HTTP Handlers (`.ashx`) for this feature into API controller actions
8. Register all services in DI following destination's existing registration pattern

> **Note:** Data access layer migration (ADO.NET → EF Core, stored procedures) is handled in the dedicated **Data Access Migration** section below — do not duplicate that work here.

### Data Access Migration

Migrate **all** data access from the Web Forms project into EF Core in the destination Web API project:

> **CRITICAL:** Web Forms projects commonly use ADO.NET directly, typed DataSets, LINQ to SQL, or Entity Framework 6. All of these must be migrated to EF Core in the destination Web API project.

1. **Analyze source data access patterns** — Identify all connection strings in `Web.config`, all `SqlConnection`/`SqlCommand` usage, all typed DataSets (`.xsd`), all EF6 `DbContext` classes, all LINQ to SQL `DataContext` classes, all stored procedure calls.

2. **Analyze destination's existing data layer** — Check if a DbContext already exists in the Web API project, its location, namespace, and configuration style (Fluent API vs data annotations, `OnModelCreating` vs separate `IEntityTypeConfiguration<T>` classes).

3. **Create entity models from source schema** — For each database table accessed by the Web Forms app:
   - If source has EF6 entities or LINQ to SQL classes, translate them to EF Core entities (update attribute namespaces, navigation property syntax, etc.)
   - If source uses ADO.NET/DataSets, reverse-engineer entity classes from the SQL schema (table columns → C# properties, data types, relationships)
   - If source uses typed DataSets (`.xsd`), map each `DataTable` to an entity class and each `TableAdapter` query to an EF Core LINQ query

4. **Migrate stored procedures** — For each stored procedure called from code-behind:
   - **Prefer EF Core LINQ** — Rewrite the stored procedure's logic as EF Core LINQ queries in the repository/service layer. This is the default approach.
   - **If the stored procedure contains complex business logic** (multi-step transactions, cursor operations, temp tables, dynamic SQL) that cannot be cleanly expressed in LINQ — keep the stored procedure in the database and call it via `context.Database.ExecuteSqlRawAsync()` or `FromSqlRaw()` from EF Core. Document which procedures were kept and why.
   - **Map `SqlDataReader` result sets** to strongly-typed entity/DTO classes.
   - **Map `DataSet`/`DataTable` results** to `List<Entity>` or `List<Dto>`.

5. **Migrate inline SQL** — All `SqlCommand` with inline SQL strings → EF Core LINQ queries. Preserve the exact query semantics (WHERE clauses, JOINs, GROUP BY, ORDER BY, subqueries).

6. **Migrate DataSet/DataTable operations** — `DataTable.Select()`, `DataRow` manipulation, `DataView` filtering/sorting → standard LINQ operations on `IQueryable<T>` or `List<T>`.

7. **Migrate entity configurations** — Create `IEntityTypeConfiguration<T>` classes for each entity, replicating the database schema (column types, constraints, indexes, relationships, default values).

8. **Migrate seed data** — If the source has SQL scripts for seed data or `Application_Start` seeding logic, create EF Core `HasData()` seed configurations.

9. **Update connection strings** — Move connection strings from `Web.config` `<connectionStrings>` to `appsettings.json` / `appsettings.Development.json` in the Web API project.

10. **Create EF Core migrations** — Generate an initial migration in the destination project.

11. **Migrate query filters** — If the source uses global filtering logic (soft delete, tenant isolation), implement as EF Core global query filters in `OnModelCreating`.

12. **Register DbContext in DI** — Follow destination's existing registration pattern (`AddDbContext`, `AddDbContextPool`, `AddDbContextFactory`).

### Auth Migration

> **Web Forms Authentication → JWT Bearer**

Web Forms typically uses **FormsAuthentication** (cookie-based, configured in `Web.config` `<authentication mode="Forms">`), ASP.NET Membership, ASP.NET Identity, or Windows Authentication. Migrate to JWT Bearer authentication:

- **FormsAuthentication** — `FormsAuthentication.SetAuthCookie()` / `FormsAuthentication.SignOut()` → JWT token generation on login, token validation middleware on API
- **`[Authorize]` on pages** (via `<authorization>` in `Web.config` `<location>` elements or page-level checks) → `[Authorize]` attribute on API controllers/actions
- **Role-based access** (`User.IsInRole("Admin")`, `<allow roles="Admin">`) → `[Authorize(Roles = "Admin")]` or policy-based authorization in Web API
- **Membership/Identity provider** — If source uses ASP.NET Membership (`Membership.ValidateUser()`, `MembershipUser`), migrate user data to ASP.NET Core Identity tables or a custom JWT user store. If source uses ASP.NET Identity (OWIN-based), migrate to ASP.NET Core Identity.
- **`Login.aspx` / `LoginStatus` / `LoginView` controls** → JWT login endpoint in Web API + frontend login page
- **`Session["UserId"]` / `Session["UserName"]`** for user context → JWT claims (`ClaimTypes.NameIdentifier`, `ClaimTypes.Name`)
- **`Web.config` `<authorization>` rules** → Inventory all `<allow>`/`<deny>` rules and translate to API `[Authorize]` attributes with matching roles/policies

### CORS Verification

Verify the Web API's CORS policy explicitly allows the frontend project's origin (development and production URLs). If not configured, add a CORS policy in `Program.cs` before migration proceeds — all API calls from the frontend will fail without it.

### Middleware Pipeline Ordering

When migrating HTTP Modules and Global.asax handlers into the destination Web API's `Program.cs` (or `Startup.cs`), ensure the middleware is registered in the correct order. The standard ASP.NET Core pipeline order is:

1. `UseExceptionHandler` / global error handling middleware (replaces `Application_Error`)
2. `UseHsts` / `UseHttpsRedirection`
3. `UseStaticFiles` (if serving static files from Web API)
4. `UseRouting`
5. `UseCors` (**must** come after `UseRouting` and before `UseAuthentication`)
6. `UseAuthentication` (replaces FormsAuthentication module)
7. `UseAuthorization`
8. Custom middleware (logging, URL rewriting, tenant resolution, etc.) — migrated from HTTP Modules; place after auth unless the module explicitly ran before authentication
9. `MapControllers` / `MapHub<T>` / endpoint mapping

If the destination project already has a configured pipeline, insert migrated middleware at the appropriate position — do not reorder existing middleware.

### HTTP Module → Middleware Migration

For each HTTP Module registered in `Web.config` `<system.webServer><modules>`:
- **Authentication modules** → `UseAuthentication()` / custom auth middleware
- **URL rewriting modules** → `UseRewriter()` middleware or custom routing middleware
- **Logging/audit modules** → Custom middleware wrapping `RequestDelegate`
- **Compression modules** → `UseResponseCompression()` middleware
- **Error handling modules** → `UseExceptionHandler()` middleware
- **Custom security modules** → Custom middleware in the pipeline

### HTTP Handler → Controller Migration

For each HTTP Handler (`.ashx`) or handler registered in `Web.config`:
- **File download handlers** → API controller action returning `FileContentResult` / `FileStreamResult`
- **Image generation handlers** → API controller action returning `FileResult` with appropriate content type
- **AJAX data handlers** (JSON/XML responders) → Standard API controller actions with `[FromQuery]`/`[FromBody]` parameters
- **Report generation handlers** → API controller action returning PDF/Excel via `FileResult`

### SignalR Migration (if inventoried in Phase 1)

> **Note:** Web Forms may use the older `Microsoft.AspNet.SignalR` (ASP.NET SignalR 2.x). This must be migrated to ASP.NET Core SignalR (`Microsoft.AspNetCore.SignalR`), which has API differences.

- Migrate all SignalR hubs to ASP.NET Core SignalR hub classes in the Web API project
- `GlobalHost.ConnectionManager` → inject `IHubContext<T>` via DI
- `Hub.Context.User` → `Context.User` (same in Core, but claims-based)
- `Clients.All.broadcastMessage(...)` → `Clients.All.SendAsync("broadcastMessage", ...)`
- Ensure `AddSignalR()` is registered and `MapHub<T>()` is mapped in `Program.cs`
- Ensure CORS policy allows credentials (`AllowCredentials()`) for SignalR connections
- Remove `<script>` references to `/signalr/hubs` (auto-generated proxy) — use `@microsoft/signalr` npm package instead

> **[ANGULAR ONLY]** — Web API side complete. The Angular service wrapping `HubConnection` from `@microsoft/signalr` is created in **Phase 3** as part of the frontend migration.

> **[REACT ONLY]** — Web API side complete. The React hook wrapping `HubConnection` from `@microsoft/signalr` is created in **Phase 3** as part of the frontend migration.

### Background Tasks Migration (if inventoried in Phase 1)

- Migrate `Timer`-based background tasks from `Global.asax` `Application_Start` → `IHostedService` / `BackgroundService` in Web API
- Migrate `Thread` / `ThreadPool.QueueUserWorkItem` background work → `IHostedService` with proper cancellation tokens
- Migrate third-party schedulers (Quartz.NET, Hangfire) into the Web API project
- Update schedules and connection strings as needed

### Web Service Migration (if inventoried in Phase 1)

- **`.asmx` SOAP services** — For each `[WebMethod]`:
  1. Create an equivalent REST API endpoint (POST for operations, GET for queries)
  2. Replace SOAP XML serialization with JSON serialization
  3. Migrate the business logic from the `[WebMethod]` into a service class
  4. If external consumers depend on the SOAP endpoint, coordinate with the user on backward compatibility
- **WCF service references** — Replace `ServiceReference` proxy classes with `HttpClient` calls to equivalent REST endpoints (or if WCF services are also being modernized, create REST endpoints in the Web API)

### File Upload Migration (if inventoried in Phase 1)

- Migrate `<asp:FileUpload>` / `RadAsyncUpload` / `AjaxFileUpload` → Web API endpoints accepting `[FromForm] IFormFile`
- **`FileUpload.SaveAs(Server.MapPath("~/uploads/"))` → destination's file storage approach** (local disk, Azure Blob, S3, etc.)
- Preserve file size limits (check `Web.config` `<httpRuntime maxRequestLength>` / `<requestLimits maxAllowedContentLength>`), file type validations
- Return file URLs or identifiers via API response; the frontend will handle display

> **[ANGULAR ONLY]** — Create an Angular upload component using Kendo Upload (`<kendo-upload>`) if Kendo is installed, or a custom file input with `HttpClient` `FormData` upload. Show progress indicators if the source Web Forms app had them.

> **[REACT ONLY]** — Create a React upload component using Kendo Upload (`<Upload>`) if Kendo is installed, or a custom `<input type="file">` with `axios` `FormData` upload (if axios is not installed, use native `fetch`). Show progress indicators if the source Web Forms app had them.

### Custom Error Pages Migration

- Migrate custom error pages from `Web.config` `<customErrors>` (`defaultRedirect`, `<error statusCode="404" redirect="...">`) into the frontend and Web API:

> **[ANGULAR ONLY]** — Create Angular error page components and configure a wildcard route (`**`) for 404. Add an HTTP interceptor (or extend the existing one) to catch `401`, `403`, and `5xx` API responses and redirect to the appropriate error component or display an error notification.

> **[REACT ONLY]** — Create React error page components and configure a catch-all `<Route path="*">` for 404. Add an axios response interceptor (or extend the existing one) to catch `401`, `403`, and `5xx` API responses and redirect to the appropriate error page or display an error notification.

- Preserve the same error page design/layout from the source Web Forms app (apply CSS migration rules).

### API Error Handling & ProblemDetails Display

> **STRICT:** When the Web API returns validation errors (HTTP 400) via `ProblemDetails` or `ValidationProblemDetails`, the frontend must parse and display these errors **inline next to the corresponding form fields** — not as a generic toast or alert. This ensures server-side validation failures are surfaced with the same UX as the source's ASP.NET validator controls displayed errors.

> **[ANGULAR ONLY]:**
> - In the Angular service or HTTP interceptor, catch `400` responses and extract the `errors` object from `ProblemDetails` (`{ "errors": { "FieldName": ["Error message"] } }`)
> - Map each error key to the corresponding `FormControl` and call `setErrors()` to display server-side errors inline
> - For non-field-level errors (business rule violations), display via notification service or a form-level error summary

> **[REACT ONLY]:**
> - In the API service / submit handler, catch `400` responses and extract the `errors` object from `ProblemDetails`
> - Map each error key to the corresponding field and call `setError('fieldName', { message: '...' })` from `react-hook-form` to display server-side errors inline
> - For non-field-level errors, display via toast notification or a form-level error summary

### Localization / i18n Migration (if inventoried in Phase 1)

- If the source Web Forms app uses `.resx` resource files (`App_LocalResources`, `App_GlobalResources`), `GetLocalResourceObject()`, `GetGlobalResourceObject()`, `meta:resourcekey` attributes:
  - Extract all localized strings into structured JSON files or the destination's i18n format
  - Migrate server-side localized validation messages to API DTOs (use `WithMessage()` with localized strings or `IStringLocalizer` in FluentValidation)

> **[ANGULAR ONLY]** — Priority: (1) `@ngx-translate/core` if already installed, (2) Angular built-in `@angular/localize` / `$localize` if project uses it, (3) default to `@ngx-translate/core`. Create translation JSON files per locale. Replace all hardcoded UI strings with translation keys.

> **[REACT ONLY]** — Priority: (1) `react-i18next` if already installed, (2) `react-intl` if already installed, (3) default to `react-i18next`. Create translation JSON files per locale. Replace all hardcoded UI strings with translation hooks (`t('key')` / `useTranslation()`).

- If the source has no localization, skip this section entirely.

### Environment Configuration (all environments)

- **Migrate `Web.config` settings to `appsettings.json`:**
  - `<connectionStrings>` → `"ConnectionStrings"` section
  - `<appSettings>` → `"AppSettings"` or feature-specific configuration sections
  - Authentication settings → JWT configuration section
  - Custom config sections → strongly-typed `IOptions<T>` configuration classes

- Configure API base URLs for **all environments**, not just development:

> **[ANGULAR ONLY]:**
> - `environment.ts` (local dev), `environment.development.ts`, `environment.staging.ts` (if applicable), `environment.prod.ts` — each with the correct API URL for that environment.

> **[REACT ONLY]:**
> - `.env.local`, `.env.development`, `.env.staging` (if applicable), `.env.production` — each with the correct API URL (`VITE_API_URL` / `REACT_APP_API_URL`).

- On the Web API side, ensure `appsettings.json`, `appsettings.Development.json`, `appsettings.Staging.json` (if applicable), and `appsettings.Production.json` have correct CORS origins, connection strings, and JWT settings for each environment.

---

## Phase 3: Frontend — Web Forms Pages → [SELECTED_FRAMEWORK]

---

### Auth UI Migration (both frameworks)

> **Migrate auth pages first, before any other pages.** Route guards and protected routes depend on the auth flow being in place.

If the source Web Forms app has `Login.aspx`, `Register.aspx`, or account management pages (or uses `<asp:Login>`, `<asp:CreateUserWizard>`, `<asp:LoginView>` controls), migrate them as the first feature in Phase 3:

> **[ANGULAR ONLY]**
> - Create a login/register component with a Reactive Form
> - On successful login, store the JWT token in `localStorage` (default; use `sessionStorage` only if the source used `FormsAuthentication` with non-persistent cookies) and redirect
> - Create an `HttpInterceptor` that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present in the destination project)
> - Create a `CanActivateFn` route guard that checks for a valid token and redirects to login if missing

> **[REACT ONLY]**
> - Create login/register page components with `react-hook-form`
> - On successful login, store the JWT token in `localStorage` (default; use `sessionStorage` only if the source used non-persistent cookies). If the destination project already uses a state store (Zustand, Redux, Context), store the token there instead. Redirect via `useNavigate()`.
> - Configure an axios interceptor (or `fetch` wrapper if axios is not installed) that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present)
> - Create a protected route component that checks for a valid token and redirects to login if missing

---

### [ANGULAR ONLY] — Web Forms → Angular Mapping

| Web Forms | Angular |
|---|---|
| **Page Structure** | |
| Master Page (`.master`) | App shell + shared header/sidebar/footer (match destination layout) |
| `<asp:ContentPlaceHolder>` / `<asp:Content>` | `<router-outlet>` — content placeholder becomes routed content |
| `.aspx` page + code-behind | Angular component (`.ts` + `.html` + `.css`) |
| User Control (`.ascx`) | Child component with `@Input` / `@Output` |
| `<%@ Page MasterPageFile="..." %>` | Component within layout route |
| **Data Binding** | |
| `<%# Eval("PropertyName") %>` | `{{ item.propertyName }}` interpolation |
| `<%# Bind("PropertyName") %>` | `<input formControlName="propertyName">` (two-way binding) |
| `<%= expression %>` | `{{ expression }}` interpolation |
| `<%: htmlEncodedExpression %>` | `{{ expression }}` (Angular auto-escapes by default) |
| **Form Controls** | |
| `<asp:TextBox>` | `<input formControlName>` — use Kendo textbox only if Kendo is installed |
| `<asp:TextBox TextMode="MultiLine">` | `<textarea formControlName>` (Kendo `<kendo-textarea>` if Kendo installed) |
| `<asp:TextBox TextMode="Password">` | `<input type="password" formControlName>` |
| `<asp:DropDownList>` | Kendo `<kendo-dropdownlist>` if Kendo installed, otherwise Angular Material `<mat-select>`, otherwise native `<select>` |
| `<asp:ListBox>` | `<select multiple formControlName>` (Kendo `<kendo-multiselect>` if Kendo installed) |
| `<asp:CheckBox>` | `<input type="checkbox" formControlName>` (Kendo `<kendo-checkbox>` if Kendo installed) |
| `<asp:CheckBoxList>` | `*ngFor` / `@for` loop of `<input type="checkbox" formControlName>` (one per item) |
| `<asp:RadioButton>` / `<asp:RadioButtonList>` | `<input type="radio" formControlName>` (one per option) |
| `<asp:HiddenField>` | `<input type="hidden" formControlName>` or component property |
| `<asp:Label>` | `<span>{{ value }}</span>` or `<label>` for form labels |
| `<asp:Literal>` | `{{ value }}` interpolation, or `[innerHTML]` if `Mode="PassThrough"` |
| `<asp:HyperLink>` | `<a [routerLink]>` |
| `<asp:Button>` / `<asp:LinkButton>` | `<button (click)="handler()">` or `<button type="submit">` in a form |
| `<asp:ImageButton>` | `<button (click)="handler()"><img src="..."></button>` |
| `<asp:FileUpload>` | `<input type="file" (change)="onFileSelect($event)">` or Kendo `<kendo-upload>` |
| `<asp:Calendar>` | `<kendo-datepicker>` if Kendo installed, otherwise `<mat-datepicker>`, otherwise `<input type="date">` |
| **Data Display** | |
| `<asp:GridView>` / `<asp:DataGrid>` | `<kendo-grid>` if Kendo installed, otherwise Angular Material Table |
| `<asp:Repeater>` | `*ngFor` / `@for` loop with a template |
| `<asp:DataList>` | `*ngFor` / `@for` loop with card/tile layout |
| `<asp:ListView>` | `*ngFor` / `@for` loop with custom template (replicate the `ItemTemplate` layout) |
| `<asp:FormView>` / `<asp:DetailsView>` | Detail component with form fields (read-only or editable based on mode) |
| `<asp:TreeView>` | `<kendo-treeview>` if Kendo installed, otherwise custom recursive component |
| `<asp:Menu>` / `<asp:SiteMapDataSource>` | Angular navigation component with `routerLink` items |
| **Validation** | |
| `<asp:RequiredFieldValidator>` | `Validators.required` on the `FormControl` + inline error display |
| `<asp:RegularExpressionValidator>` | `Validators.pattern(regex)` using the exact `ValidationExpression` |
| `<asp:RangeValidator>` | `Validators.min()` / `Validators.max()` |
| `<asp:CompareValidator>` | Custom cross-field `ValidatorFn` |
| `<asp:CustomValidator>` | Custom `ValidatorFn` (client-side) / `AsyncValidatorFn` (server-side only) |
| `<asp:ValidationSummary>` | Form-level error summary component — collect all `FormGroup` errors and display as a list |
| `ValidationGroup` | Separate `FormGroup` per validation group |
| **State & Navigation** | |
| `ViewState["key"]` | Component property (eliminated — state lives in the component) |
| `Session["key"]` | Angular service (singleton), JWT claims, or state management (NgRx if installed) |
| `Application["key"]` | API-side configuration or Angular service |
| `Request.QueryString["id"]` | `ActivatedRoute.params` / `ActivatedRoute.queryParams` |
| `Response.Redirect("page.aspx")` | `router.navigate(['/path'])` |
| `Server.Transfer("page.aspx")` | `router.navigate(['/path'])` (same as redirect from frontend perspective) |
| `IsPostBack` check | Eliminated — initial load is handled by `ngOnInit`, and button actions are explicit HTTP calls |
| **Notifications** | |
| `ScriptManager.RegisterStartupScript` (alert) | `ngx-toastr` notification or `sweetalert2` |
| `Page.ClientScript.RegisterClientScriptBlock` | Component logic in `ngOnInit` / `AfterViewInit` |
| **Misc** | |
| `<asp:Image>` | `<img [src]="imageUrl">` |
| `<asp:Panel>` | `<div>` with `[hidden]` or `*ngIf` / `@if` for visibility toggle |
| `<asp:MultiView>` / `<asp:Wizard>` | Stepper/tab component or multi-step form with route-based or state-based step navigation |
| `<asp:UpdatePanel>` | Eliminated — all data fetching is via explicit HTTP calls. No equivalent needed. |
| `<asp:Timer>` | RxJS `interval()` with `switchMap()` to poll API, or SignalR for push |
| `<asp:LoginView>` | `*ngIf` / `@if` based on auth state (e.g., `isAuthenticated` flag from auth service) |
| `<asp:LoginStatus>` | Login/Logout button toggled by auth state |
| Bing Maps (embedded via `<script>` or `<iframe>`) | **STRICT — Direct Bing Maps V8 SDK** via `bingmaps` types package. Use `Microsoft.Maps.Map` in `AfterViewInit` + `ElementRef`. API key from `environment.ts` placeholder. Do not substitute. |

### [ANGULAR ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any page):**
> - Update `environment.ts` / `environment.development.ts` with the Web API base URL if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the component structure, module pattern, and service pattern to follow for this feature
2. Create TypeScript model/interface matching the API DTO
3. Create Angular service using `HttpClient` — follow destination's existing service patterns (base URL config, error handling, interceptors)
4. Create components (list, detail, create/edit) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (lazy-loaded modules or standalone routes)
6. **Migrate ALL form validations (STRICT)** — For every ASP.NET validator control on the `.aspx` page, extract the `ControlToValidate`, `ValidationExpression`, `MinimumValue`/`MaximumValue`, `ControlToCompare`, `ErrorMessage`/`Text`, and `ValidationGroup`. Create an equivalent Angular Reactive Forms validator for **each one** — `Validators.required`, `Validators.minLength`, `Validators.maxLength`, `Validators.min`, `Validators.max`, `Validators.pattern`, custom `ValidatorFn` for cross-field rules (`CompareValidator`), custom `AsyncValidatorFn` for server-only `CustomValidator`. Preserve **all custom error messages exactly**. Display validation errors inline next to each field, matching the same positioning and timing as the source (ASP.NET validators typically show immediately next to the control). If the source uses `<asp:ValidationSummary>`, create an equivalent form-level error summary component matching the `DisplayMode`.
7. For Telerik/Kendo controls — reference the **Phase 4 Kendo Angular mapping table** for the equivalent Angular component (only if Kendo migration was confirmed in Project Paths step 4)
8. **Bing Maps migration (STRICT — Direct Bing Maps V8 SDK only)** — If the source page embeds Bing Maps (look for `Microsoft.Maps.Map` in `<script>` blocks, Bing Maps `<iframe>` embeds, or code-behind `RegisterStartupScript` with Bing Maps initialization), **migrate as-is using the Bing Maps V8 SDK directly.** Do not substitute with Google Maps, Leaflet, or any other map provider.
   - **Install:** `npm install bingmaps` (TypeScript type definitions for Bing Maps V8). Add `/// <reference types="bingmaps" />` in a global `.d.ts` file or at the top of the component file.
   - **Script loading:** Add the Bing Maps control script to `index.html` (`<script src="https://www.bing.com/api/maps/mapcontrol?callback=bingMapsReady"></script>`) or load it dynamically via an injectable `BingMapsLoaderService` that appends the script tag and resolves a Promise when the callback fires.
   - **API key handling:** Add a placeholder entry `"BingMaps": { "ApiKey": "" }` in `appsettings.json` on the Web API side. In `environment.ts`, add `bingMapsKey: ''`. The user will fill in the actual Bing Maps API key post-migration (may be found in the source `Web.config` `<appSettings>`). During migration, replicate the exact same map configuration from the source — just wire the key reference to `environment.bingMapsKey`.
   - **Component implementation:** In the Angular component, use `AfterViewInit` + `@ViewChild` with an `ElementRef` container `<div>`. Initialize the map: `new Microsoft.Maps.Map(this.mapContainer.nativeElement, { credentials: this.apiKey, center: new Microsoft.Maps.Location(lat, lng), zoom: zoomLevel, mapTypeId: Microsoft.Maps.MapTypeId.road })`. Migrate **all** map features from source:
     - **Pushpins:** `const pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, lng), { icon: iconUrl, title: title });` → `map.entities.push(pin);`
     - **Infoboxes:** `const infobox = new Microsoft.Maps.Infobox(location, { title, description, visible: false });` → `infobox.setMap(map);` → show on pushpin click via `Microsoft.Maps.Events.addHandler(pin, 'click', () => infobox.setOptions({ visible: true }))`
     - **Polylines:** `new Microsoft.Maps.Polyline([loc1, loc2, ...], { strokeColor, strokeThickness })` → `map.entities.push(polyline);`
     - **Polygons:** `new Microsoft.Maps.Polygon([loc1, loc2, ...], { fillColor, strokeColor, strokeThickness })` → `map.entities.push(polygon);`
     - **Event handlers:** `Microsoft.Maps.Events.addHandler(map, 'click', callback)` — replicate all source event handlers
   - **Cleanup:** Implement `OnDestroy` to call `map.dispose()` and remove event handlers.
   - Preserve **all** source Bing Maps functionality with exact feature parity.
9. Use other third-party controls **only if already installed** in destination (Material, etc.) — do not install new UI libraries
10. **Migrate inline `<script>` blocks and `RegisterStartupScript` calls** — All JavaScript in the `.aspx` page's `<script>` blocks, `ScriptManager.RegisterStartupScript`, `Page.ClientScript.RegisterClientScriptBlock`, and `RegisterClientScriptInclude` must be migrated into the Angular component's `ngOnInit` / `AfterViewInit` lifecycle hooks or directive logic. Do not discard page-specific JS.
11. **Migrate User Controls (`.ascx`)** — For each User Control referenced via `<%@ Register %>` and used as `<uc:ControlName>`, create a standalone Angular component. The Angular component should accept inputs matching the User Control's public properties and fetch its own data via an injected service if the User Control loaded data in `Page_Load`.
12. Migrate CSS/styles — use destination's existing styling approach. Check in order: Angular component styles (`.scss`/`.css` co-located) → global `styles.scss` → CSS Modules if configured

---

### [REACT ONLY] — Web Forms → React Mapping

| Web Forms | React |
|---|---|
| **Page Structure** | |
| Master Page (`.master`) | Root layout component + shared header/sidebar/footer |
| `<asp:ContentPlaceHolder>` / `<asp:Content>` | `<Outlet>` from `react-router-dom` — content placeholder becomes routed content |
| `.aspx` page + code-behind | React page component (`.tsx`) |
| User Control (`.ascx`) | Child component with props |
| `<%@ Page MasterPageFile="..." %>` | Component within layout route |
| **Data Binding** | |
| `<%# Eval("PropertyName") %>` | `{item.propertyName}` JSX expression |
| `<%# Bind("PropertyName") %>` | `<input {...register('propertyName')}>` (two-way via react-hook-form) |
| `<%= expression %>` | `{expression}` JSX expression |
| `<%: htmlEncodedExpression %>` | `{expression}` (React auto-escapes by default) |
| **Form Controls** | |
| `<asp:TextBox>` | `<input {...register('field')}>` — use Kendo React `<Input>` only if Kendo installed |
| `<asp:TextBox TextMode="MultiLine">` | `<textarea {...register('field')}>` (Kendo `<TextArea>` if Kendo installed) |
| `<asp:TextBox TextMode="Password">` | `<input type="password" {...register('field')}>` |
| `<asp:DropDownList>` | Kendo `<DropDownList>` if Kendo installed, otherwise `react-select`, otherwise native `<select>` |
| `<asp:ListBox>` | `<select multiple {...register('field')}>` (Kendo `<MultiSelect>` if Kendo installed) |
| `<asp:CheckBox>` | `<input type="checkbox" {...register('field')}>` (Kendo `<Checkbox>` if Kendo installed) |
| `<asp:CheckBoxList>` | `.map()` over items rendering `<input type="checkbox">` per item |
| `<asp:RadioButton>` / `<asp:RadioButtonList>` | `<input type="radio" {...register('field')}>` per option |
| `<asp:HiddenField>` | `<input type="hidden" {...register('field')}>` or component state |
| `<asp:Label>` | `<span>{value}</span>` or `<label>` for form labels |
| `<asp:Literal>` | `{value}` JSX expression, or `dangerouslySetInnerHTML` if `Mode="PassThrough"` (only if trusted) |
| `<asp:HyperLink>` | `<Link to="...">` from `react-router-dom` |
| `<asp:Button>` / `<asp:LinkButton>` | `<button onClick={handler}>` or `<button type="submit">` |
| `<asp:ImageButton>` | `<button onClick={handler}><img src="..." /></button>` |
| `<asp:FileUpload>` | `<input type="file" onChange={handleFile}>` or Kendo `<Upload>` |
| `<asp:Calendar>` | `<DatePicker>` from Kendo / MUI / `<input type="date">` |
| **Data Display** | |
| `<asp:GridView>` / `<asp:DataGrid>` | `<Grid>` from Kendo if installed, otherwise MUI DataGrid, otherwise `@tanstack/react-table` |
| `<asp:Repeater>` | `{items.map(item => <Component key={item.id} {...item} />)}` |
| `<asp:DataList>` | `.map()` with card/tile layout |
| `<asp:ListView>` | `.map()` with custom template (replicate the `ItemTemplate` layout) |
| `<asp:FormView>` / `<asp:DetailsView>` | Detail component with form fields (read-only or editable based on mode) |
| `<asp:TreeView>` | `<TreeView>` from Kendo if installed, otherwise custom recursive component |
| `<asp:Menu>` / `<asp:SiteMapDataSource>` | Navigation component with `<Link>` items |
| **Validation** | |
| `<asp:RequiredFieldValidator>` | `yup.string().required('message')` (zod: `z.string().min(1, 'message')`) |
| `<asp:RegularExpressionValidator>` | `.matches(regex, message)` using exact `ValidationExpression` (zod: `.regex()`) |
| `<asp:RangeValidator>` | `.min()` / `.max()` with original messages |
| `<asp:CompareValidator>` | `.oneOf([yup.ref('field')])` or `.test()` for cross-field (zod: `.refine()`) |
| `<asp:CustomValidator>` | Custom `yup.test()` (client-side) / async `.test()` (server-only) |
| `<asp:ValidationSummary>` | Form-level error summary — collect all `formState.errors` and display as list |
| `ValidationGroup` | Separate `yup` schema per validation group |
| **State & Navigation** | |
| `ViewState["key"]` | Component `useState` (eliminated — state lives in the component) |
| `Session["key"]` | React Context, Zustand/Redux store, or JWT claims |
| `Application["key"]` | API-side configuration or React Context |
| `Request.QueryString["id"]` | `useParams()` / `useSearchParams()` from `react-router-dom` |
| `Response.Redirect("page.aspx")` | `useNavigate()` from `react-router-dom` |
| `Server.Transfer("page.aspx")` | `useNavigate()` (same as redirect from frontend perspective) |
| `IsPostBack` check | Eliminated — initial load via `useEffect`, actions are explicit handlers |
| **Notifications** | |
| `ScriptManager.RegisterStartupScript` (alert) | `react-toastify` notification or `sweetalert2` |
| `Page.ClientScript.RegisterClientScriptBlock` | Component logic in `useEffect` |
| **Misc** | |
| `<asp:Image>` | `<img src={imageUrl} />` |
| `<asp:Panel>` | `<div>` with conditional rendering `{show && <div>...</div>}` |
| `<asp:MultiView>` / `<asp:Wizard>` | Stepper/tab component or multi-step form with state-based navigation |
| `<asp:UpdatePanel>` | Eliminated — all data fetching via explicit API calls. No equivalent needed. |
| `<asp:Timer>` | `useEffect` with `setInterval` for polling, or SignalR for push |
| `<asp:LoginView>` | Conditional rendering based on auth state `{isAuth ? <Dashboard /> : <Login />}` |
| `<asp:LoginStatus>` | Login/Logout button toggled by auth state |
| Bing Maps (embedded via `<script>` or `<iframe>`) | **STRICT — Direct Bing Maps V8 SDK** via `bingmaps` types package. Use `Microsoft.Maps.Map` in `useEffect` + `useRef<HTMLDivElement>`. API key from env config placeholder. Do not substitute. |

### [REACT ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any page):**
> - Update `.env` / `.env.development` with the Web API base URL (`VITE_API_URL` or `REACT_APP_API_URL`) if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the page/component structure, routing setup, and data-fetching pattern to follow for this feature
2. Create TypeScript interface matching the API DTO
3. Create API service / custom hook (`useQuery`, `useMutation`, or custom `useXxx` hook) — follow destination's existing data-fetching patterns; include error handling (catch API errors and display via toast or inline message)
4. Create page and child components (list, detail, create/edit form) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (`react-router-dom` v6 `<Route>`, nested routes, or file-based routing)
6. **Migrate ALL form validations (STRICT)** — For every ASP.NET validator control on the `.aspx` page, extract the `ControlToValidate`, `ValidationExpression`, `MinimumValue`/`MaximumValue`, `ControlToCompare`, `ErrorMessage`/`Text`, and `ValidationGroup`. Create an equivalent `yup` schema rule (default; use `zod` only if already installed and `yup` is not) for **each one** — `.required()`, `.min()`, `.max()`, `.matches()`, `.oneOf()` for cross-field, `.test()` for custom/async. Preserve **all custom error messages exactly**. Display validation errors inline next to each field using `formState.errors`, matching the same positioning as the source's ASP.NET validators. If the source uses `<asp:ValidationSummary>`, create an equivalent form-level error summary component.
7. For Telerik/Kendo controls — reference the **Phase 4 Kendo React mapping table** for the equivalent React component (only if Kendo migration was confirmed in Project Paths step 4)
8. **Bing Maps migration (STRICT — Direct Bing Maps V8 SDK only)** — If the source page embeds Bing Maps, **migrate as-is using the Bing Maps V8 SDK directly.** Do not substitute with any other map provider.
   - **Install:** `npm install bingmaps` (TypeScript type definitions for Bing Maps V8). Add `/// <reference types="bingmaps" />` in a global `.d.ts` file.
   - **Script loading:** Load the Bing Maps control script dynamically in a custom hook (`useBingMapsLoader`) or a `useEffect` — append `<script src="https://www.bing.com/api/maps/mapcontrol?callback=bingMapsReady"></script>` to document head and resolve via the callback. Clean up the script tag in the `useEffect` cleanup.
   - **API key handling:** Add a placeholder entry `VITE_BINGMAPS_KEY=` (Vite) or `REACT_APP_BINGMAPS_KEY=` (CRA) in `.env`. The user will fill in the actual key post-migration (may be found in `Web.config` `<appSettings>`).
   - **Component implementation:** Create a reusable `BingMap` component. Use `useRef<HTMLDivElement>(null)` for the map container. In `useEffect` (after script loaded), initialize: `new Microsoft.Maps.Map(ref.current, { credentials: apiKey, center: new Microsoft.Maps.Location(lat, lng), zoom: zoomLevel, mapTypeId: Microsoft.Maps.MapTypeId.road })`. Migrate **all** map features from source:
     - **Pushpins:** `const pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, lng), { icon: iconUrl, title });` → `map.entities.push(pin);`
     - **Infoboxes:** `const infobox = new Microsoft.Maps.Infobox(location, { title, description, visible: false });` → `infobox.setMap(map);` → show on pushpin click
     - **Polylines:** `new Microsoft.Maps.Polyline([loc1, loc2, ...], { strokeColor, strokeThickness })` → `map.entities.push(polyline);`
     - **Polygons:** `new Microsoft.Maps.Polygon([loc1, loc2, ...], { fillColor, strokeColor, strokeThickness })` → `map.entities.push(polygon);`
     - **Event handlers:** `Microsoft.Maps.Events.addHandler(map, 'click', callback)` — replicate all source event handlers
   - **Cleanup:** In the `useEffect` cleanup function, call `map.dispose()` and remove event handlers to prevent memory leaks.
   - Preserve **all** source Bing Maps functionality with exact feature parity.
9. Use other third-party controls **only if already installed** in destination (MUI, Ant Design, etc.) — do not install new UI libraries
10. **Migrate inline `<script>` blocks and `RegisterStartupScript` calls** — All JavaScript in the `.aspx` page's `<script>` blocks, `ScriptManager.RegisterStartupScript`, `Page.ClientScript.RegisterClientScriptBlock`, and `RegisterClientScriptInclude` must be migrated into the React component's `useEffect` hooks, event handlers, or custom hooks. Do not discard page-specific JS.
11. **Migrate User Controls (`.ascx`)** — For each User Control referenced via `<%@ Register %>` and used as `<uc:ControlName>`, create a standalone React component. The React component should accept props matching the User Control's public properties and fetch its own data via a custom hook if the User Control loaded data in `Page_Load`.
12. Migrate CSS/styles — use destination's existing styling approach. Check in order: CSS Modules (if `.module.css` files exist) → Tailwind (if `tailwind.config` exists) → styled-components (if installed) → plain CSS files

---

### Static Assets & CSS Migration

> **STRICT REQUIREMENT:** Migrate the **entire CSS** from the source Web Forms project. Every stylesheet referenced in Master Pages, `<link>` tags in `.aspx` pages, `App_Themes` folder, inline `<style>` blocks, and `ScriptManager` bundles must be accounted for. The destination frontend must reproduce the **same visual design, layout, spacing, colors, typography, and responsive behavior** as the source application. Do not discard, simplify, or "modernize" styles — preserve full visual fidelity.

**CSS Migration Steps:**

1. **Inventory all CSS sources** — Collect every CSS file from the project root, `App_Themes/` folder (if using ASP.NET themes), `Content/` or `Styles/` folders, `<link>` references in Master Pages and `.aspx` pages, inline `<style>` blocks, `ScriptManager` `CompositeScript` bundles, and `Web.config` bundling configurations.
2. **Map CSS to destination structure** — Move all stylesheets into the destination project's styling location. Maintain the same file organization.
3. **Preserve all class names and selectors** — Keep the same CSS class names so that migrated HTML/components render identically. Do not rename classes unless the destination project enforces scoped styles (CSS Modules, Angular `ViewEncapsulation`), in which case map every class explicitly.
4. **Migrate page-specific and control-specific styles** — Any CSS scoped to a specific `.aspx` page or `.ascx` control must be co-located with the equivalent frontend component.
5. **Migrate media queries and responsive breakpoints** — Preserve all `@media` rules exactly as defined in the source.
6. **Migrate CSS variables and theming** — If the source uses CSS custom properties, `App_Themes` folder with `.skin` files, or Telerik theme CSS, replicate them in the destination's theming setup.
7. **Migrate vendor/third-party CSS** — If the source includes Bootstrap, Telerik CSS theme, Font Awesome, or other library stylesheets, ensure the same versions or equivalent styles are included in the destination project.
8. **Remove Web Forms-specific JS** — Remove `WebResource.axd`, `ScriptResource.axd`, `MicrosoftAjax.js`, `MicrosoftMvcValidation.js`, ASP.NET AJAX client library, and other framework JS files. Do **not** remove any CSS that was loaded alongside those scripts.
9. **Migrate custom JavaScript** — For each custom `.js` file in the source project, identify its purpose. jQuery and jQuery plugin files are removed (replaced by framework equivalents). Custom JS files containing business logic, page initialization, or utility functions must be migrated into the appropriate component/hook/service in the destination frontend. Do not silently drop any JS file without confirming its logic is covered by the migrated components.
10. **Visual verification** — After migration, every page/component should visually match the source Web Forms application. Flag any CSS that could not be migrated 1:1 and note the deviation.

Move images and static assets → destination's assets location. Use destination's existing asset pipeline for images and static files.

---

## Phase 4: Telerik / Kendo Component Reference (Used During Phase 3)

> **This is a reference section, not a standalone execution phase.** Phase 3 Per-View Steps point here whenever a Telerik/Kendo control needs to be replaced. Only apply if Telerik/Kendo migration was confirmed in Project Paths step 4.

### [ANGULAR ONLY] — Kendo Angular Reference

Apply this phase only if Kendo migration was confirmed and packages were set up in the Project Paths section (step 4). By this point, `@progress/kendo-angular-*` packages are already installed in the destination project.

| Web Forms Telerik / Kendo Control | Angular Kendo |
|---|---|
| `RadGrid` / `<asp:GridView>` with Telerik skin | `<kendo-grid>` |
| `RadComboBox` / `RadDropDownList` | `<kendo-dropdownlist>` / `<kendo-combobox>` |
| `RadDatePicker` / `RadDateTimePicker` | `<kendo-datepicker>` / `<kendo-datetimepicker>` |
| `RadNumericTextBox` | `<kendo-numerictextbox>` |
| `RadChart` / `RadHtmlChart` | `<kendo-chart>` |
| `RadAsyncUpload` / `RadUpload` | `<kendo-upload>` |
| `RadWindow` / `RadAlert` / `RadConfirm` | `<kendo-dialog>` (default). Use `DialogService` only if destination already uses programmatic dialog opening. |
| `RadTabStrip` | `<kendo-tabstrip>` |
| `RadPanelBar` | `<kendo-panelbar>` from `@progress/kendo-angular-layout` |
| `RadTreeView` | `<kendo-treeview>` |
| `RadEditor` | `<kendo-editor>` |
| `RadScheduler` | `<kendo-scheduler>` from `@progress/kendo-angular-scheduler` |
| `RadAutoCompleteBox` | `<kendo-autocomplete>` from `@progress/kendo-angular-dropdowns` |
| `RadMaskedTextBox` | `<kendo-maskedtextbox>` from `@progress/kendo-angular-inputs` |
| `RadToolBar` | `<kendo-toolbar>` from `@progress/kendo-angular-toolbar` |
| `RadMenu` | `<kendo-menu>` from `@progress/kendo-angular-menu` |
| `RadListBox` | `<kendo-listbox>` from `@progress/kendo-angular-listbox` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side.

---

### [REACT ONLY] — Kendo React Reference

Apply this phase only if Kendo migration was confirmed and packages were set up in the Project Paths section (step 4). By this point, `@progress/kendo-react-*` packages are already installed in the destination project.

| Web Forms Telerik / Kendo Control | React Kendo |
|---|---|
| `RadGrid` / `<asp:GridView>` with Telerik skin | `<Grid>` from `@progress/kendo-react-grid` |
| `RadComboBox` / `RadDropDownList` | `<DropDownList>` / `<ComboBox>` from `@progress/kendo-react-dropdowns` |
| `RadDatePicker` / `RadDateTimePicker` | `<DatePicker>` / `<DateTimePicker>` from `@progress/kendo-react-dateinputs` |
| `RadNumericTextBox` | `<NumericTextBox>` from `@progress/kendo-react-inputs` |
| `RadChart` / `RadHtmlChart` | `<Chart>` from `@progress/kendo-react-charts` |
| `RadAsyncUpload` / `RadUpload` | `<Upload>` from `@progress/kendo-react-upload` |
| `RadWindow` / `RadAlert` / `RadConfirm` | `<Dialog>` from `@progress/kendo-react-dialogs` |
| `RadTabStrip` | `<TabStrip>` from `@progress/kendo-react-layout` |
| `RadPanelBar` | `<PanelBar>` from `@progress/kendo-react-layout` |
| `RadTreeView` | `<TreeView>` from `@progress/kendo-react-treeview` |
| `RadEditor` | `<Editor>` from `@progress/kendo-react-editor` |
| `RadScheduler` | `<Scheduler>` from `@progress/kendo-react-scheduler` |
| `RadAutoCompleteBox` | `<AutoComplete>` from `@progress/kendo-react-dropdowns` |
| `RadMaskedTextBox` | `<MaskedTextBox>` from `@progress/kendo-react-inputs` |
| `RadToolBar` | `<ToolBar>` from `@progress/kendo-react-buttons` |
| `RadMenu` | `<Menu>` from `@progress/kendo-react-layout` |
| `RadListBox` | `<ListBox>` from `@progress/kendo-react-listbox` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side (same as Angular).

---

## Phase 5: Per-Page Checklist

> **Complete the one-time setup below once before starting any page migration. Then use the per-page checklist for each page.**

**One-Time Setup — [ANGULAR ONLY]:**
- [ ] `environment.ts` / `environment.development.ts` / `environment.staging.ts` / `environment.prod.ts` API base URLs set for all environments
- [ ] Auth pages (login/register) migrated, JWT storage in place (replaces FormsAuthentication)
- [ ] `HttpInterceptor` attaching `Authorization: Bearer` header
- [ ] `HttpInterceptor` handling `400` ProblemDetails — maps server validation errors to form controls via `setErrors()`
- [ ] `HttpInterceptor` handling `401`, `403`, `5xx` — redirect to error pages or display notification
- [ ] `CanActivateFn` route guard for protected routes (replaces `Web.config` `<authorization>` rules)
- [ ] Custom error page components (404, 500, AccessDenied) with wildcard route
- [ ] SignalR Angular service created using `@microsoft/signalr` (if applicable — replaces `Microsoft.AspNet.SignalR` client)
- [ ] Localization setup — `@ngx-translate/core` (default) or `@angular/localize` (if project uses it) with translation JSON files (if source uses `.resx` resources)
- [ ] Bing Maps one-time setup — `npm install bingmaps`, `/// <reference types="bingmaps" />` in global `.d.ts`, Bing Maps script loaded in `index.html` or via `BingMapsLoaderService`, `bingMapsKey: ''` placeholder in `environment.ts`, `"BingMaps": { "ApiKey": "" }` in `appsettings.json` (if source uses Bing Maps)

**One-Time Setup — [REACT ONLY]:**
- [ ] `.env.local` / `.env.development` / `.env.staging` / `.env.production` API base URLs set for all environments
- [ ] Auth pages (login/register) migrated, JWT storage in place (replaces FormsAuthentication)
- [ ] Axios interceptor (or equivalent) attaching `Authorization: Bearer` header
- [ ] Axios interceptor handling `400` ProblemDetails — maps server validation errors to form fields via `setError()`
- [ ] Axios interceptor handling `401`, `403`, `5xx` — redirect to error pages or display notification
- [ ] Protected route component for guarded routes (replaces `Web.config` `<authorization>` rules)
- [ ] Custom error page components (404, 500, AccessDenied) with catch-all route
- [ ] SignalR React hook created using `@microsoft/signalr` (if applicable — replaces `Microsoft.AspNet.SignalR` client)
- [ ] Localization setup — `react-i18next` (default) or `react-intl` (only if already installed and react-i18next is not) with translation JSON files (if source uses `.resx` resources)
- [ ] Bing Maps one-time setup — `npm install bingmaps`, `/// <reference types="bingmaps" />` in global `.d.ts`, Bing Maps loader hook/utility created, `VITE_BINGMAPS_KEY=` or `REACT_APP_BINGMAPS_KEY=` placeholder in `.env`, `"BingMaps": { "ApiKey": "" }` in `appsettings.json` (if source uses Bing Maps)

---

**Per-Page — Backend (both frameworks):**
- [ ] API Controller with endpoints for all page data operations (replaces code-behind event handlers)
- [ ] Services + Interfaces — business logic extracted from code-behind
- [ ] DTOs + AutoMapper profile (follow destination DTO patterns)
- [ ] All server-side validations migrated (ASP.NET validators → data annotations/FluentValidation on DTOs) — return `ValidationProblemDetails` on failure
- [ ] HTTP Handlers (`.ashx`) for this feature migrated to controller actions
- [ ] Data access migrated — ADO.NET/DataSets/EF6/stored procedures → EF Core queries and entities (data layer is migrated as part of the per-page backend work; `DbContext` registration is one-time setup)
- [ ] Stored procedures reviewed — migrated to LINQ or kept and documented
- [ ] Register services in DI
- [ ] File upload endpoints migrated (`FileUpload` → `[FromForm] IFormFile`) with validation (if applicable)
- [ ] Localized validation messages and resource strings migrated (if applicable)
- [ ] SignalR hub migrated to ASP.NET Core SignalR + CORS credentials allowed (if applicable)
- [ ] Background tasks migrated to `IHostedService` (if applicable)
- [ ] `Web.config` settings for this feature migrated to `appsettings.*.json` for all environments

**Per-Page — Frontend [ANGULAR ONLY]:**
- [ ] TypeScript models/interfaces
- [ ] Angular Service with `HttpClient` (follow destination service pattern)
- [ ] Components (list, detail, create/edit matching source page functionality)
- [ ] Feature routing — lazy-loaded modules or standalone routes
- [ ] **ALL client-side validations migrated** — every `RequiredFieldValidator`, `RegularExpressionValidator`, `RangeValidator`, `CompareValidator`, `CustomValidator` → Reactive Forms `ValidatorFn` / `AsyncValidatorFn` with exact error messages preserved
- [ ] `ValidationSummary` migrated to form-level error summary (if applicable)
- [ ] Validation error display matches source UX (inline errors next to each control)
- [ ] **API ProblemDetails errors displayed inline** — server-side 400 validation errors mapped to form controls via `setErrors()`
- [ ] `UpdatePanel` async postbacks replaced with proper HTTP calls (if applicable)
- [ ] ViewState/Session state replaced with component state / Angular services
- [ ] File upload component migrated (if applicable)
- [ ] Localized UI strings migrated to translation files (if applicable)
- [ ] Telerik/Kendo controls replaced using Phase 4 reference table (if confirmed)
- [ ] Bing Maps component migrated using Direct Bing Maps V8 SDK — all features replicated (if applicable)
- [ ] SignalR Angular service wired into component (if applicable)
- [ ] Migrate CSS/SCSS styles
- [ ] Inline `<script>` and `RegisterStartupScript` logic migrated to component lifecycle
- [ ] User Controls (`.ascx`) migrated to Angular child components
- [ ] E2E test full flow

**Per-Page — Frontend [REACT ONLY]:**
- [ ] TypeScript interfaces
- [ ] API service / custom hook (axios, React Query, etc. — follow destination pattern)
- [ ] Page and child components (matching source page functionality)
- [ ] Feature routing — `react-router-dom` routes (follow destination routing pattern)
- [ ] **ALL client-side validations migrated** — every `RequiredFieldValidator`, `RegularExpressionValidator`, `RangeValidator`, `CompareValidator`, `CustomValidator` → `yup` schema rules (or `zod` if already installed) with exact error messages preserved
- [ ] `ValidationSummary` migrated to form-level error summary (if applicable)
- [ ] Validation error display matches source UX (inline errors next to each control)
- [ ] **API ProblemDetails errors displayed inline** — server-side 400 validation errors mapped to form fields via `setError()`
- [ ] `UpdatePanel` async postbacks replaced with proper HTTP calls (if applicable)
- [ ] ViewState/Session state replaced with component `useState` / React Context
- [ ] File upload component migrated (if applicable)
- [ ] Localized UI strings migrated to translation files (if applicable)
- [ ] Telerik/Kendo controls replaced using Phase 4 reference table (if confirmed)
- [ ] Bing Maps component migrated using Direct Bing Maps V8 SDK — all features replicated (if applicable)
- [ ] SignalR React hook wired into component (if applicable)
- [ ] Migrate CSS/styles — use destination's existing styling approach (CSS Modules → Tailwind → styled-components → plain CSS)
- [ ] Inline `<script>` and `RegisterStartupScript` logic migrated to `useEffect`/handlers
- [ ] User Controls (`.ascx`) migrated to React child components
- [ ] E2E test full flow

**Order:** Core/Auth first → then remaining pages in **alphabetical order** → Complex features last (SignalR, file uploads, heavy AJAX). Within each feature: List/Grid page → Details page → Create/Add page → Edit page → Delete page → remaining pages alphabetically.

**After ALL pages are fully migrated (backend + frontend):**
- Mark Phase 2, Phase 3, and Phase 5 as `[x] COMPLETED` in `MIGRATION_PROGRESS.md`
- Update "Last Updated" timestamp
- Print final summary: total pages migrated, total files created, any skipped items
- **Do NOT delete `MIGRATION_PROGRESS.md`** — keep it as a migration audit trail. The user may delete it manually when satisfied.

---

## Quick Reference: Key Transformations

**Backend (both frameworks):**

| Web Forms | Web API |
|---|---|
| Code-behind (`.aspx.cs` / `.aspx.vb`) | API Controllers + Service Layer |
| `Page_Load` + `!IsPostBack` | GET endpoints returning JSON |
| Button click handlers | POST/PUT/DELETE endpoints |
| GridView event handlers | GET with paging/sorting/filtering params |
| ADO.NET / DataSets / EF6 | EF Core |
| Stored procedures (inline SQL) | EF Core LINQ queries (or `FromSqlRaw` for complex procs) |
| FormsAuthentication | JWT Bearer |
| `Session["key"]` | JWT claims / `IMemoryCache` |
| `ViewState["key"]` | Eliminated (frontend state) |
| `Web.config` connection strings | `appsettings.json` |
| `Web.config` `<appSettings>` | `IOptions<T>` / `IConfiguration` |
| `Web.config` `<authorization>` | `[Authorize]` attributes / policy-based auth |
| HTTP Modules | ASP.NET Core Middleware |
| HTTP Handlers (`.ashx`) | API Controller actions |
| `Global.asax` events | `Program.cs` configuration + middleware |
| `.asmx` Web Services | REST API Controllers |
| `Response.Redirect` / `Server.Transfer` | HTTP status codes (frontend routes) |
| `UpdatePanel` async postback | Proper REST API calls |
| `Application_Error` | Exception handling middleware |
| SignalR 2.x hubs | ASP.NET Core SignalR hubs |
| Background `Timer` / `Thread` | `IHostedService` / `BackgroundService` |

**Frontend — [ANGULAR ONLY]:**

| Web Forms | Angular |
|---|---|
| `.aspx` pages | Angular Components (`.ts` + `.html`) |
| Code-behind data classes | TS Interfaces |
| Server controls (`<asp:*>`) | Angular form controls + Kendo Angular |
| ASP.NET Validators | Angular Reactive Forms `ValidatorFn` |
| `ValidationSummary` | Form-level error summary component |
| Master Pages (`.master`) | App shell + shared layout components |
| User Controls (`.ascx`) | Child components (`@Input`/`@Output`) |
| `ViewState` / `Session` | Component state / Angular services / JWT claims |
| `Response.Redirect` | `router.navigate()` |
| `UpdatePanel` | Explicit HTTP calls via `HttpClient` |
| `IsPostBack` | `ngOnInit` for initial load; explicit handlers for actions |
| `ScriptManager` JS alerts | `ngx-toastr` / `sweetalert2` |
| jQuery / vanilla JS | RxJS, Angular directives, Angular pipes |
| `<asp:LoginView>` | `*ngIf` / `@if` based on auth state |
| `<asp:GridView>` data binding | Kendo Grid or Angular Material Table |
| `<asp:Repeater>` / `<asp:DataList>` | `*ngFor` / `@for` loop |
| `AutoPostBack` dropdowns | `(change)` event → HTTP call |
| `<asp:Timer>` polling | RxJS `interval()` + `switchMap()` |

**Frontend — [REACT ONLY]:**

| Web Forms | React |
|---|---|
| `.aspx` pages | React Components (`.tsx`) |
| Code-behind data classes | TS Interfaces |
| Server controls (`<asp:*>`) | React form components + Kendo React |
| ASP.NET Validators | `react-hook-form` + `yup` (default; `zod` if installed) |
| `ValidationSummary` | Form-level error summary component |
| Master Pages (`.master`) | Root layout component |
| User Controls (`.ascx`) | Child components (props) |
| `ViewState` / `Session` | `useState` / React Context / Zustand/Redux |
| `Response.Redirect` | `useNavigate()` from `react-router-dom` |
| `UpdatePanel` | Explicit HTTP calls via axios/fetch |
| `IsPostBack` | `useEffect` for initial load; explicit handlers for actions |
| `ScriptManager` JS alerts | `react-toastify` / `sweetalert2` |
| jQuery / vanilla JS | Custom hooks, utility functions |
| `<asp:LoginView>` | Conditional rendering `{isAuth ? ... : ...}` |
| `<asp:GridView>` data binding | Kendo Grid or MUI DataGrid or TanStack Table |
| `<asp:Repeater>` / `<asp:DataList>` | `.map()` rendering |
| `AutoPostBack` dropdowns | `onChange` handler → API call |
| `<asp:Timer>` polling | `useEffect` + `setInterval` |
