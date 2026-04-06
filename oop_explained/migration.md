# ASP.NET Core MVC → Angular / React + Web API Migration Plan

## Determinism & Consistency Rules

> **CRITICAL — READ FIRST:** This migration plan must produce **identical output** every time it is executed against the same source and destination projects. Follow these rules to eliminate variation:

### Decision Resolution Order

When this document offers multiple alternatives (separated by `/`, `or`, or listed in a table), **never pick randomly**. Always resolve using this strict priority:

1. **Use what is already installed in the destination project.** Scan `package.json` (frontend) and `.csproj` (Web API) for installed packages. If a package is already present, use it — no exceptions.
2. **If nothing is installed, use the first option listed** in this document. The first option in every list, table cell, or slash-separated pair is the **default**. Only use a later option if the first is explicitly incompatible with the destination project's framework version.
3. **Never introduce a new library** that is not already installed in the destination project and not listed as the first option in this document.

### Processing Order

- **Phase execution:** Always execute Phase 1 → Phase 2 → Phase 3 → Phase 5 in strict order. Phase 4 is a reference table consulted during Phase 3 only.
- **Controller processing order:** Process controllers in this order: **Auth/Account controllers first** (login, register, account management — needed before other features), then remaining controllers in **alphabetical order by controller name** (e.g., `DashboardController` before `OrderController`), then complex feature controllers last (SignalR-heavy, file-upload-heavy). Within each controller, process actions in the order they appear in the source file, top to bottom.
- **View processing order:** For each controller, process views in this fixed order: Index/List → Details → Create → Edit → Delete → any remaining views alphabetically.
- **Service/DTO creation order:** Create services and DTOs in the same order as their associated controllers are processed.

### Naming Conventions (deterministic)

All generated file and symbol names must follow these exact rules — no creative renaming:

> **[ANGULAR ONLY]:**
> - Component: `{source-view-name}.component.ts` (kebab-case) — e.g., `student-list.component.ts`, `student-detail.component.ts`
> - Service: `{controller-name}.service.ts` — e.g., `student.service.ts`
> - Model/Interface: `{dto-name}.model.ts` — e.g., `student.model.ts`
> - Module (if NgModule): `{feature-name}.module.ts` — e.g., `student.module.ts`
> - Guard: `{feature-name}.guard.ts` — e.g., `auth.guard.ts`
> - Interceptor: `{purpose}.interceptor.ts` — e.g., `auth.interceptor.ts`, `error.interceptor.ts`
> - Folder structure: `src/app/{feature-name}/` — one folder per MVC controller

> **[REACT ONLY]:**
> - Page component: `{SourceViewName}Page.tsx` (PascalCase) — e.g., `StudentListPage.tsx`, `StudentDetailPage.tsx`
> - Component: `{SourceViewName}.tsx` — e.g., `StudentForm.tsx`
> - Hook: `use{Feature}.ts` — e.g., `useStudents.ts`
> - Service: `{feature}Service.ts` (default). Use `{feature}Api.ts` only if the destination project already uses the `*Api.ts` naming pattern.
> - Model/Interface: `{dto-name}.types.ts` — e.g., `student.types.ts`
> - Folder structure: `src/pages/{feature-name}/` for pages, `src/components/{feature-name}/` for shared components — one folder per MVC controller

> **Web API (both frameworks):**
> - Controller: `{SourceControllerName}Controller.cs` → `{Same}Controller.cs` (keep original name)
> - DTO: `{SourceViewModelName}Dto.cs` — replace `ViewModel` suffix with `Dto`
> - Service interface: `I{ServiceName}.cs` (keep original name)
> - Service implementation: `{ServiceName}.cs` (keep original name)
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
- Source MVC: [path]
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

## Controller Migration Status
<!-- One row per controller, alphabetical order. Update status after EACH controller completes. -->
<!-- Column mapping to Phase 5 per-controller checklist:
  Backend API = API Controller + custom middleware/filters
  Backend Data = Entities, EF configs, seed data, interceptors, query filters for this controller's domain (DbContext registration is one-time setup)
  Backend Services = Services + Interfaces + DTOs + AutoMapper profile + DI registration + appsettings
  Backend Validations = All server-side validations + localized messages
  Frontend Components = TS interfaces/models + service/hook + page components + routing
  Frontend Validations = Client-side validations + ProblemDetails inline display
  Frontend Features = File upload, SignalR, localization, Kendo controls, CSS (if applicable)
-->
| Controller | Backend API | Backend Data | Backend Services | Backend Validations | Frontend Components | Frontend Validations | Frontend Features | Status |
|---|---|---|---|---|---|---|---|---|
| AccountController | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | NOT STARTED |
| DashboardController | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | NOT STARTED |
| ... | | | | | | | | |

## Current Position
- **Currently working on:** [Phase X, ControllerName, Step Y]
- **Next step:** [description of what to do next]
- **Last completed file:** [path of last file created/modified]
```

### Checkpoint Rules

1. **Update `MIGRATION_PROGRESS.md` after every completed unit of work.** A unit of work is:
   - Completing a phase
   - Completing one-time setup items
   - Completing a controller's backend migration (all backend checklist items for that controller)
   - Completing a controller's frontend migration (all frontend checklist items for that controller)
   - Completing any standalone section (CSS migration, error pages, etc.)

2. **Always update the "Current Position" section** before starting any new unit of work, so that if the session breaks mid-work, the resume knows exactly where to pick up.

3. **Mark checkboxes as `[x]`** in the tracker as each item completes. Never uncheck a completed item.

### How to Resume After a Break

> **USER INSTRUCTION:** If the migration was interrupted by a session timeout, paste this entire `migration.md` prompt into the new session and add the line: **"Resume the migration — check MIGRATION_PROGRESS.md for the checkpoint."** The AI will then follow the resume protocol below.

When a session starts (or is restarted after a timeout/break), **before doing anything else**, follow these steps:

1. **Check if `MIGRATION_PROGRESS.md` exists** in the destination frontend project root.

2. **If it does NOT exist** — this is a fresh migration. Proceed normally from the "Workspace Modification Permission" section.

3. **If it DOES exist** — this is a **resume**. Do the following:
   a. Read `MIGRATION_PROGRESS.md` completely.
   b. Read the "Session Info" section to restore all project paths, framework choice, and Kendo settings — **do NOT re-ask the user for these**.
   c. Read "Phase Status" to determine which phase is current.
   d. Read "Controller Migration Status" to determine which controllers are already done.
   e. Read "Current Position" to determine exactly where to resume.
   f. **Verify the last completed work** — check that the files listed as "Last completed file" actually exist and are valid. If the last unit was interrupted mid-way (file exists but is incomplete), redo only that unit.
   g. **Print a resume summary** to the user:
      ```
      Resuming migration from checkpoint:
      - Phase: [X]
      - Last completed: [controller/step]
      - Next: [controller/step]
      - Controllers done: [N of M]
      ```
   h. **Ask the user:** "Resume from this checkpoint? (yes / restart from scratch)"
   i. If **yes** — continue from the "Next step" recorded in the tracker. Do not repeat completed work.
   j. If **restart** — delete `MIGRATION_PROGRESS.md` and start fresh from "Workspace Modification Permission".

### Preventing Session Timeout

To minimize the risk of session breaks during large migrations:

1. **Work in small atomic units.** Complete ONE controller's backend migration fully, update the tracker, then proceed to the next. Do not batch multiple controllers.

2. **Do not generate large code blocks without saving.** After generating each file, write it to disk immediately. Do not accumulate multiple files in memory before writing.

3. **Prefer multiple small file writes over one massive output.** If a controller has 4 components, write each component file individually rather than generating all 4 at once.

4. **After every 3 controllers completed**, print a brief status update to the user:
   ```
   Progress: [N/M] controllers migrated. Checkpoint saved.
   ```

5. **If the migration has more than 10 controllers**, process them in batches of 5. After each batch:
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

1. First, ask: **"Please provide the full path to the Source ASP.NET Core MVC project:"** — Wait for response, validate the path exists and contains a `.csproj` file.

2. Then ask for the destination frontend project path based on the selected framework:

   > **[ANGULAR ONLY]** — "Please provide the full path to the Destination Angular project:" — Validate the path exists and contains a `package.json` and `angular.json`.

   > **[REACT ONLY]** — "Please provide the full path to the Destination React project:" — Validate the path exists and contains a `package.json` and either `vite.config.ts`, `vite.config.js`, or `react-scripts` in dependencies.

3. Then ask: **"Please provide the full path to the Destination C# Web API project:"** — Wait for response, validate the path exists and contains a `.csproj` file.

Do not proceed with any migration until all three paths are collected and validated.

4. Then ask: **"Does the source MVC application use Kendo UI? (yes/no):"**

   - If **yes** — ask: **"Which version of Kendo UI is used in the source project? (e.g., 2023.1, 2024.2 — check `bower.json`, `package.json`, or the Kendo CDN script version):"**
     - Use the provided version as a reference for feature parity when selecting equivalent Kendo components in the destination project.

   > **[ANGULAR ONLY] — If yes:**
   > - Check whether `@progress/kendo-angular-*` packages already exist in the destination project's `package.json`.
   > - **If already installed** — use the installed version as-is. Do **not** run any install commands. Skip the version question below.
   > - **If not installed** — ask: **"Which version of Kendo Angular do you want to install in the destination project? (e.g., 16.x, 17.x — or press Enter to install latest):"**
   >   - Use the specified version when installing packages (e.g., `@progress/kendo-angular-grid@16.x`). If no version is given, install the latest compatible with the project's Angular version.
   >   - Install only the specific Kendo Angular packages needed for the controls being migrated (e.g., `@progress/kendo-angular-grid`, `@progress/kendo-angular-dropdowns`). Do not install the entire Kendo suite.
   > - Note: This is a one-time setup step only. Continue with Phase 1 → 2 → 3 in order. Phase 4's Kendo Angular control mapping table will be referenced **during Phase 3** whenever a Kendo MVC control is encountered — do not skip ahead to Phase 4.

   > **[ANGULAR ONLY] — If no:** Skip Phase 4 and use standard HTML/Angular Material controls based on what's installed in the destination Angular project.

   > **[REACT ONLY] — If yes:**
   > - Check whether `@progress/kendo-react-*` packages already exist in the destination project's `package.json`.
   > - **If already installed** — use the installed version as-is. Do **not** run any install commands. Skip the version question below.
   > - **If not installed** — ask: **"Which version of Kendo React do you want to install in the destination project? (e.g., 8.x, 9.x — or press Enter to install latest):"**
   >   - Use the specified version when installing packages (e.g., `@progress/kendo-react-grid@8.x`). If no version is given, install the latest compatible with the project's React version.
   >   - Install only the specific Kendo React packages needed for the controls being migrated (e.g., `@progress/kendo-react-grid`, `@progress/kendo-react-dropdowns`). Do not install the entire Kendo suite.
   > - Note: This is a one-time setup step only. Continue with Phase 1 → 2 → 3 in order. Phase 4's Kendo React control mapping table will be referenced **during Phase 3** whenever a Kendo MVC control is encountered — do not skip ahead to Phase 4.

   > **[REACT ONLY] — If no:** Skip Phase 4 and use standard HTML/React controls (Material UI, Ant Design, etc.) based on what's installed in the destination React project.

---

## Overview

Migrate monolithic MVC app into: **[SELECTED_FRAMEWORK]** (existing project, UI) + **C# Web API** (existing project, backend).

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

- **All server-side validations (STRICT — migrate every rule)** — Data annotations (`[Required]`, `[StringLength]`, `[Range]`, `[RegularExpression]`, `[Compare]`, `[EmailAddress]`, `[Phone]`, `[CreditCard]`, `[Url]`, etc.), FluentValidation rules (all `RuleFor` chains including `.Must()`, `.When()`, `.Unless()`, `.WithMessage()`), custom `IValidatableObject` implementations, action filter validations, custom `ValidationAttribute` subclasses → migrate **all** to API DTOs with identical rules (server-side). Do not skip, simplify, or weaken any validation rule. Every field constraint, conditional rule, cross-field comparison, and custom error message must be preserved exactly.
- **All client-side validations (STRICT — migrate every rule to the frontend):**
  > **CRITICAL:** Every validation that executes in the browser in the source MVC app must have a corresponding client-side validator in the destination frontend. This includes: jQuery Unobtrusive Validation attributes (`data-val-*`), `data-val-required`, `data-val-length`, `data-val-range`, `data-val-regex`, `data-val-equalto`, `data-val-remote` (async), custom `$.validator.addMethod()` / `$.validator.unobtrusive.adapters.add()` validators, inline JavaScript validation, and any custom validation logic in `.js` files. **No validation may exist only on the server — if it was client-side in MVC, it must remain client-side in the destination.**

  > **[ANGULAR ONLY]** Migrate every client-side validation rule to Angular Reactive Forms:
  > - `data-val-required` → `Validators.required`
  > - `data-val-length-max` / `data-val-length-min` → `Validators.minLength()` / `Validators.maxLength()`
  > - `data-val-range-min` / `data-val-range-max` → `Validators.min()` / `Validators.max()`
  > - `data-val-regex-pattern` → `Validators.pattern()`
  > - `data-val-equalto` → custom cross-field `ValidatorFn` (e.g., password confirmation match)
  > - `data-val-remote` → custom `AsyncValidatorFn` calling the equivalent API endpoint
  > - Custom `$.validator.addMethod()` → custom `ValidatorFn` with the same logic
  > - All custom error messages (`data-val-*` messages) → `{ errorKey: 'Exact same error message' }` in the validator or displayed via `<mat-error>` / custom error component
  > - Conditional validations (`.When()` / `.Unless()` in FluentValidation reflected client-side) → `ValidatorFn` that checks the condition at runtime

  > **[REACT ONLY]** Migrate every client-side validation rule to `react-hook-form` + `yup` schema (default; use `zod` only if `zod` is already installed in the destination and `yup` is not):
  > - `data-val-required` → `yup.string().required('message')` (if using zod: `z.string().min(1, 'message')`)
  > - `data-val-length-max` / `data-val-length-min` → `.min()` / `.max()` with original messages
  > - `data-val-range-min` / `data-val-range-max` → `.min()` / `.max()` on number schema
  > - `data-val-regex-pattern` → `.matches(pattern, message)` (if using zod: `z.string().regex()`)
  > - `data-val-equalto` → `.oneOf([yup.ref('field')])` (if using zod: `zod.refine()`) for cross-field match
  > - `data-val-remote` → custom async validation via `yup.test()` calling the API endpoint (if using zod: `zod.refine()`)
  > - Custom `$.validator.addMethod()` → custom `yup.test()` with the same logic (if using zod: `zod.refine()`)
  > - All custom error messages → preserved exactly in the schema `.required('Same message')` / `.min(n, 'Same message')`
  > - Conditional validations → `.when()` in yup (if using zod: `.refine()` with conditional logic)
- **AutoMapper profiles** — All entity↔ViewModel mappings → entity↔DTO AutoMapper profiles in Web API
- **Custom middleware** — Exception handling, request logging, tenant resolution, rate limiting, etc. → Web API middleware pipeline
- **Custom action filters** — Authorization filters, validation filters, audit filters → Web API `IActionFilter` / `IAsyncActionFilter` / middleware
- **Custom exception filters** — `IExceptionFilter` implementations → Web API exception handling middleware or filters
- **Custom result filters** — `IResultFilter` implementations → Web API equivalent filters
- **Custom model binders** — `IModelBinder` implementations → Web API custom model binders or `[FromBody]`/`[FromQuery]` with DTOs
- **Custom tag helpers** and **custom HTML helpers:**
  > **[ANGULAR ONLY]** → Angular directives, pipes, or Kendo Angular components
  > **[REACT ONLY]** → React components, custom hooks, or utility functions
- **Custom validation attributes** — `[CustomValidation]`, `ValidationAttribute` subclasses → API: custom validation attributes on DTOs + frontend: custom validator functions
- **Business rule validations** — Service-layer validations, domain validations → preserve in Web API services, surface errors via `ProblemDetails` to the frontend
- **All DbContext classes & EF Core configuration** — Migrate every DbContext, entity configurations, seeding, and migrations into the destination Web API project following its existing data layer structure
- **SignalR hubs** (if present) — Keep hubs in Web API; create a frontend service/hook to connect via `@microsoft/signalr`
- **Background jobs** (if present) — Migrate Hangfire, Quartz.NET, or `IHostedService` / `BackgroundService` classes into the Web API project

---

## Phase 1: Analyze Source MVC App

Inventory all: Controllers (actions, routes, `[Authorize]`), Razor Views (layouts, partials, ViewComponents, tag helpers), View Models, EF Core entities/DbContext, Services, Static assets, Third-party libs (Kendo, Bing Maps, etc.), Middleware/Filters, Custom Validations, AutoMapper profiles, SignalR hubs, Background jobs.

**Before proceeding to Phase 2, produce an inventory summary** listing:
- All controllers and their action count
- All Razor views grouped by controller
- All ViewComponents (classes inheriting `ViewComponent` / `IViewComponentResult`) and where they are invoked
- All EF Core entities and DbContext classes
- All third-party libraries detected
- All client-side validations — list every form with its `data-val-*` rules, custom `$.validator.addMethod()` validators, `data-val-remote` endpoints, and inline JS validation logic
- All server-side validations — data annotations on ViewModels/entities, FluentValidation validators, custom `ValidationAttribute` subclasses, `IValidatableObject` implementations
- All AutoMapper profiles and entity↔ViewModel mappings
- All SignalR hubs (if any)
- All background jobs (if any)
- Any custom middleware, filters, or validation attributes
- All MVC Areas and their controllers/views (if any)
- All file upload endpoints (`IFormFile` parameters, multipart form handling)
- All custom error pages (404, 500, AccessDenied, etc.)
- Localization/i18n usage — `.resx` resource files, `IStringLocalizer`, `IHtmlLocalizer`, `data-val-*` localized messages (if any)
- `_ViewImports.cshtml` — list all `@using`, `@addTagHelper`, and `@inject` directives (these define global tag helper registrations and namespace imports that affect every view)
- `_ViewStart.cshtml` — note the default layout assignment and any startup logic
- All JavaScript bundles from `bundleconfig.json` / `_BundleConfig.cs` — list each bundle's input files and what they do (jQuery plugins, page-specific scripts, custom validators, etc.)

Present this summary to the user and wait for confirmation before beginning Phase 2.

**After user confirms the inventory:** Create `MIGRATION_PROGRESS.md` in the destination frontend project root (see **Session Resilience & Checkpoint Resume** section for exact format). Populate the "Session Info", mark Phase 1 as `[x] COMPLETED`, and populate the "Controller Migration Status" table with all controllers from the inventory in alphabetical order, all marked `NOT STARTED`.

**Library Mapping:**

> **[ANGULAR ONLY]**

> Resolution: Use the **first** package in the "Angular Equivalent" column. If it is not installed and not compatible, try the next. See **Determinism & Consistency Rules** above.

| MVC Library | Angular Equivalent (priority order — use first match) |
|---|---|
| Kendo UI / Telerik | `@progress/kendo-angular-*` |
| Bootstrap | 1. `@ng-bootstrap/ng-bootstrap` → 2. `ngx-bootstrap` |
| jQuery Validation | Angular Reactive Forms (built-in, no package needed) |
| DataTables | 1. `@progress/kendo-angular-grid` (if Kendo confirmed) → 2. Angular Material Table |
| Select2 | 1. `@progress/kendo-angular-dropdowns` (if Kendo confirmed) → 2. Angular Material Autocomplete |
| Chart.js/Highcharts | 1. `@progress/kendo-angular-charts` (if Kendo confirmed) → 2. `ngx-charts` |
| Toastr / SweetAlert | 1. `ngx-toastr` → 2. `sweetalert2` |
| Bing Maps | **STRICT — must use Bing Maps V8 SDK directly.** Install `bingmaps` types (`npm install bingmaps`). Load the Bing Maps script (`https://www.bing.com/api/maps/mapcontrol`) in `index.html` or dynamically via a service. Read the API key from `environment.ts` (placeholder `bingMapsKey: ''` — user will add the actual key to `appsettings.json` post-migration). Use `Microsoft.Maps.Map` API in `AfterViewInit` with `ElementRef`. Do not substitute with Google Maps, Leaflet, or any other map provider. |

---

> **[REACT ONLY]**

> Resolution: Use the **first** package in the "React Equivalent" column. If it is not installed and not compatible, try the next. See **Determinism & Consistency Rules** above.

| MVC Library | React Equivalent (priority order — use first match) |
|---|---|
| Kendo UI / Telerik | `@progress/kendo-react-*` |
| Bootstrap | 1. `react-bootstrap` → 2. `reactstrap` |
| jQuery Validation | `react-hook-form` + `yup` (default). Use `zod` only if `zod` is already installed and `yup` is not. |
| DataTables | 1. `@progress/kendo-react-grid` (if Kendo confirmed) → 2. MUI DataGrid → 3. `@tanstack/react-table` |
| Select2 | 1. `react-select` → 2. `@progress/kendo-react-dropdowns` (if Kendo confirmed) |
| Chart.js/Highcharts | 1. `@progress/kendo-react-charts` (if Kendo confirmed) → 2. `recharts` → 3. `@nivo/core` |
| Toastr / SweetAlert | 1. `react-toastify` → 2. `sweetalert2` |
| Bing Maps | **STRICT — must use Bing Maps V8 SDK directly.** Install `bingmaps` types (`npm install bingmaps`). Load the Bing Maps script (`https://www.bing.com/api/maps/mapcontrol`) dynamically in a `useEffect` hook. Read the API key from environment config (`VITE_BINGMAPS_KEY` or `REACT_APP_BINGMAPS_KEY` — user will add the actual key post-migration; use a placeholder during migration). Use `Microsoft.Maps.Map` on a `useRef<HTMLDivElement>` container. Do not substitute with Google Maps, Leaflet, or any other map provider. |

---

## Phase 2: Backend — MVC Controllers → Web API

*(Applies to both Angular and React — no framework-specific differences)*

### Controller Conversion Rules

- `Controller` → `ControllerBase` with `[ApiController]`, `[Route("api/[controller]")]`
- `return View(...)` → `return Ok(...)` (JSON responses)
- `RedirectToAction(...)` → proper status codes (`CreatedAtAction`, `NoContent`, `NotFound`, `BadRequest`)
- Remove `[ValidateAntiForgeryToken]` (JWT handles security); preserve `[Authorize]` attributes
- `[ApiController]` auto-validates ModelState; remove manual `ModelState.IsValid` checks
- ViewModels → DTOs, mapped via AutoMapper profiles

### Per-Controller Steps

1. Create API controller following **destination project's existing controller conventions**
2. Move/adapt Service interfaces & implementations into destination's service layer structure
3. Create DTOs following destination's existing DTO patterns; add AutoMapper profiles to existing profile structure
4. Migrate all validations (data annotations, FluentValidation, custom attributes) to DTOs
5. Migrate custom action/exception/result filters into destination's filter or middleware structure
6. Migrate custom model binders if applicable
7. Register all services in DI following destination's existing registration pattern

> **Note:** Entity models, DbContext, and connection strings are handled in the dedicated **DbContext & EF Core Migration** section below — do not duplicate that work here.

### DbContext & EF Core Migration

Migrate **all** DbContext classes and EF Core data layer into the destination Web API project:

1. **Analyze destination's existing data layer** — Check if a DbContext already exists, its location, namespace, and configuration style (Fluent API vs data annotations, `OnModelCreating` vs separate `IEntityTypeConfiguration<T>` classes)
2. **Migrate all entity models** — Copy all EF Core entity classes into destination's entity/model folder, preserving relationships, navigation properties, and data annotations
3. **Migrate DbContext classes** — If source has a single DbContext, merge its `DbSet<>` properties and configurations into destination's existing DbContext. If source has multiple DbContexts (e.g., `ApplicationDbContext`, `IdentityDbContext`, `TenantDbContext`), migrate each one respecting destination's pattern
4. **Migrate entity configurations** — Move all `IEntityTypeConfiguration<T>` classes or `OnModelCreating` Fluent API configurations into destination's configuration folder/structure
5. **Migrate seed data** — Move `HasData()` seed configurations or custom `IDbSeeder` classes
6. **Migrate repository layer** — If source uses Repository/Unit of Work pattern, move repositories into destination's existing repository structure. If destination uses DbContext directly, adapt accordingly
7. **Update connection strings** — Update `appsettings.json` / `appsettings.Development.json` with correct connection strings
8. **Regenerate migrations** — Create a fresh initial migration in the destination project (`dotnet ef migrations add InitialMigration`) or migrate existing migration history
9. **Migrate query filters** — Global query filters (soft delete, tenant isolation) from `OnModelCreating`
10. **Migrate interceptors** — EF Core `SaveChangesInterceptor`, `DbCommandInterceptor` for audit trails, soft delete, etc.
11. **Register DbContext in DI** — Follow destination's existing registration pattern (`AddDbContext`, `AddDbContextPool`, `AddDbContextFactory`)

### Auth Verification

Verify JWT Bearer, Role/Policy `[Authorize]` attributes, and claims mapping match the MVC app.

### CORS Verification

Verify the Web API's CORS policy explicitly allows the frontend project's origin (development and production URLs). If not configured, add a CORS policy in `Program.cs` before migration proceeds — all API calls from the frontend will fail without it.

### Middleware Pipeline Ordering

When migrating custom middleware into the destination Web API's `Program.cs` (or `Startup.cs`), ensure the middleware is registered in the correct order. The standard ASP.NET Core pipeline order is:

1. `UseExceptionHandler` / global error handling middleware
2. `UseHsts` / `UseHttpsRedirection`
3. `UseStaticFiles` (if serving static files from Web API)
4. `UseRouting`
5. `UseCors` (**must** come after `UseRouting` and before `UseAuthentication`)
6. `UseAuthentication`
7. `UseAuthorization`
8. Custom middleware (logging, tenant resolution, rate limiting, etc.) — place after auth unless the middleware explicitly needs to run before authentication
9. `MapControllers` / `MapHub<T>` / endpoint mapping

If the destination project already has a configured pipeline, insert migrated middleware at the appropriate position — do not reorder existing middleware.

### SignalR Migration (if inventoried in Phase 1)

- Keep all SignalR hubs in the Web API project
- Ensure `AddSignalR()` is registered and `MapHub<T>()` is mapped in `Program.cs`
- Ensure CORS policy allows credentials (`AllowCredentials()`) for SignalR connections

> **[ANGULAR ONLY]** — Web API side complete. The Angular service wrapping `HubConnection` from `@microsoft/signalr` is created in **Phase 3** as part of the frontend migration.

> **[REACT ONLY]** — Web API side complete. The React hook wrapping `HubConnection` from `@microsoft/signalr` is created in **Phase 3** as part of the frontend migration.

### Background Jobs Migration (if inventoried in Phase 1)

- Migrate Hangfire, Quartz.NET, or `IHostedService` / `BackgroundService` classes into the Web API project
- Follow the destination Web API's existing background job registration pattern
- Update job schedules and connection strings as needed

### File Upload Migration (if inventoried in Phase 1)

- Migrate all `IFormFile` / `IFormFileCollection` action parameters to Web API endpoints accepting `[FromForm]` multipart data
- Preserve file size limits, allowed file type validations, and virus scan integrations
- If the source stores files to `wwwroot/uploads/` or a local path, update to the destination's file storage approach (local disk, Azure Blob, S3, etc.)
- Return file URLs or identifiers via API response; the frontend will handle display

> **[ANGULAR ONLY]** — Create an Angular upload component using Kendo Upload (`<kendo-upload>`) if Kendo is installed, or a custom file input with `HttpClient` `FormData` upload. Show progress indicators if the source MVC app had them.

> **[REACT ONLY]** — Create a React upload component using Kendo Upload (`<Upload>`) if Kendo is installed, or a custom `<input type="file">` with `axios` `FormData` upload (if axios is not installed, use native `fetch`). Show progress indicators if the source MVC app had them.

### MVC Areas Migration (if inventoried in Phase 1)

- Map each MVC Area to a dedicated routing module/section in the frontend:

> **[ANGULAR ONLY]** — Each MVC Area → a lazy-loaded Angular feature module or standalone route group under a matching URL prefix (e.g., `/admin/...`, `/portal/...`). Create area-specific layout components if the source Area has its own `_Layout.cshtml`.

> **[REACT ONLY]** — Each MVC Area → a nested route group in `react-router-dom` under a matching URL prefix. Create area-specific layout components if the source Area has its own `_Layout.cshtml`.

- On the Web API side, Area controllers become API controllers under `[Route("api/[area]/[controller]")]` or the destination's existing route prefix convention.

### Custom Error Pages Migration

- Migrate custom error pages (`404 Not Found`, `500 Internal Server Error`, `403 AccessDenied`, `401 Unauthorized`, etc.) from the source MVC app:

> **[ANGULAR ONLY]** — Create Angular error page components and configure a wildcard route (`**`) for 404. Add an HTTP interceptor (or extend the existing one) to catch `401`, `403`, and `5xx` API responses and redirect to the appropriate error component or display an error notification.

> **[REACT ONLY]** — Create React error page components and configure a catch-all `<Route path="*">` for 404. Add an axios response interceptor (or extend the existing one) to catch `401`, `403`, and `5xx` API responses and redirect to the appropriate error page or display an error notification.

- Preserve the same error page design/layout from the source MVC app (apply CSS migration rules).

### API Error Handling & ProblemDetails Display

> **STRICT:** When the Web API returns validation errors (HTTP 400) via `ProblemDetails` or `ValidationProblemDetails`, the frontend must parse and display these errors **inline next to the corresponding form fields** — not as a generic toast or alert. This ensures server-side validation failures are surfaced with the same UX as client-side validation errors.

> **[ANGULAR ONLY]:**
> - In the Angular service or HTTP interceptor, catch `400` responses and extract the `errors` object from `ProblemDetails` (`{ "errors": { "FieldName": ["Error message"] } }`)
> - Map each error key to the corresponding `FormControl` and call `setErrors()` to display server-side errors inline
> - For non-field-level errors (business rule violations), display via notification service or a form-level error summary

> **[REACT ONLY]:**
> - In the API service / submit handler, catch `400` responses and extract the `errors` object from `ProblemDetails`
> - Map each error key to the corresponding field and call `setError('fieldName', { message: '...' })` from `react-hook-form` to display server-side errors inline
> - For non-field-level errors, display via toast notification or a form-level error summary

### Localization / i18n Migration (if inventoried in Phase 1)

- If the source MVC app uses `.resx` resource files, `IStringLocalizer<T>`, `IHtmlLocalizer<T>`, or `IViewLocalizer`:
  - Extract all localized strings into structured JSON files or the destination's i18n format
  - Migrate server-side localized validation messages to API DTOs (use `WithMessage()` with localized strings or `IStringLocalizer` in FluentValidation)

> **[ANGULAR ONLY]** — Priority: (1) `@ngx-translate/core` if already installed, (2) Angular built-in `@angular/localize` / `$localize` if project uses it, (3) default to `@ngx-translate/core`. Create translation JSON files per locale. Replace all hardcoded UI strings with translation keys.

> **[REACT ONLY]** — Priority: (1) `react-i18next` if already installed, (2) `react-intl` if already installed, (3) default to `react-i18next`. Create translation JSON files per locale. Replace all hardcoded UI strings with translation hooks (`t('key')` / `useTranslation()`).

- If the source has no localization, skip this section entirely.

### Environment Configuration (all environments)

- Configure API base URLs for **all environments**, not just development:

> **[ANGULAR ONLY]:**
> - `environment.ts` (local dev), `environment.development.ts`, `environment.staging.ts` (if applicable), `environment.prod.ts` — each with the correct API URL for that environment.

> **[REACT ONLY]:**
> - `.env.local`, `.env.development`, `.env.staging` (if applicable), `.env.production` — each with the correct API URL (`VITE_API_URL` / `REACT_APP_API_URL`).

- On the Web API side, ensure `appsettings.json`, `appsettings.Development.json`, `appsettings.Staging.json` (if applicable), and `appsettings.Production.json` have correct CORS origins, connection strings, and JWT settings for each environment.

---

## Phase 3: Frontend — Razor Views → [SELECTED_FRAMEWORK]

---

### Auth UI Migration (both frameworks)

> **Migrate auth pages first, before any other views.** Route guards and protected routes depend on the auth flow being in place.

If the source MVC app has login, register, or account management pages, migrate them as the first feature in Phase 3:

> **[ANGULAR ONLY]**
> - Create a login/register component with a Reactive Form
> - On successful login, store the JWT token in `localStorage` (default; use `sessionStorage` only if the source MVC app used session-scoped auth cookies) and redirect
> - Create an `HttpInterceptor` that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present in the destination project)
> - Create an `CanActivateFn` route guard that checks for a valid token and redirects to login if missing

> **[REACT ONLY]**
> - Create login/register page components with `react-hook-form`
> - On successful login, store the JWT token in `localStorage` (default; use `sessionStorage` only if the source MVC app used session-scoped auth cookies). If the destination project already uses a state store (Zustand, Redux, Context), store the token there instead. Redirect via `useNavigate()`.
> - Configure an axios interceptor (or `fetch` wrapper if axios is not installed) that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present)
> - Create a protected route component that checks for a valid token and redirects to login if missing

---

### [ANGULAR ONLY] — Razor → Angular Mapping

| Razor | Angular |
|---|---|
| `_Layout.cshtml` | App shell + shared header/sidebar/footer (match destination layout) |
| `@model ViewModel` | TypeScript interface |
| `@Html.TextBoxFor` | `<input formControlName>` — use Kendo textbox only if Kendo is installed in destination |
| `@Html.DropDownListFor` | Kendo `<kendo-dropdownlist>` if Kendo installed, otherwise Angular Material `<mat-select>` if installed, otherwise native `<select>` |
| `@Html.ValidationMessageFor` | Angular form error display — use destination's existing error display pattern; if none exists, use inline `<div *ngIf="control.errors">` |
| `<form asp-action>` | `<form [formGroup] (ngSubmit)>` |
| `@Html.Partial("_X", item)` | Child component with `@Input` |
| `@Html.ActionLink` | `<a [routerLink]>` |
| `@if / @foreach` | Use destination's Angular version syntax: Angular 17+ → `@if`/`@for`; Angular <17 → `*ngIf`/`*ngFor`. Check `package.json` for Angular version. |
| `ViewBag.Title` | Angular `Title` service (`import { Title } from '@angular/platform-browser'`) |
| `TempData["Msg"]` | `ngx-toastr` notification service (default). Use `sweetalert2` only if already installed and `ngx-toastr` is not. |
| `@Html.DisplayFor` | `{{ model.property }}` interpolation (read-only display) |
| `@Html.DisplayNameFor` | Label text — use `<label>` with model metadata or hardcoded label matching source |
| `@Html.EditorFor` | `<input formControlName>` (same as `TextBoxFor` unless source renders a custom editor template — replicate that template as a child component) |
| `@Html.HiddenFor` | `<input type="hidden" formControlName>` |
| `@Html.RadioButtonFor` | `<input type="radio" formControlName>` |
| `@Html.CheckBoxFor` | `<input type="checkbox" formControlName>` (Kendo `<kendo-checkbox>` if Kendo installed) |
| `@Html.TextAreaFor` | `<textarea formControlName>` (Kendo `<kendo-textarea>` if Kendo installed) |
| `@Html.LabelFor` | `<label for="controlId">` with text matching source label |
| `@Html.PasswordFor` | `<input type="password" formControlName>` |
| `@Html.ListBoxFor` | `<select multiple formControlName>` (Kendo `<kendo-multiselect>` if Kendo installed) |
| `@Html.Raw(...)` | `[innerHTML]="sanitizedHtml"` — sanitize via `DomSanitizer.bypassSecurityTrustHtml()` only if source content is trusted |
| `@Html.ValidationSummary()` | Form-level error summary component — collect all `FormGroup` errors and display as a list above the form (match source UX) |
| `ViewData["key"]` | Component property or Angular service for shared state |
| `@Url.Action("Action", "Controller")` | Build route path string using Angular Router — e.g., `'/controller/action'` or `router.createUrlTree()` |
| `@Url.Content("~/path")` | Asset path — use `assets/path` relative to `src/assets/` |
| `@Html.AntiForgeryToken()` | Not needed (JWT) |
| **ASP.NET Core Tag Helpers** | **Angular equivalents (same as `@Html.*` counterparts above):** |
| `<input asp-for="Name">` | `<input formControlName="name">` (same rules as `@Html.TextBoxFor`) |
| `<textarea asp-for="Bio">` | `<textarea formControlName="bio">` (same rules as `@Html.TextAreaFor`) |
| `<label asp-for="Name">` | `<label for="controlId">` with text matching source label (same as `@Html.LabelFor`) |
| `<select asp-for="Cat" asp-items="...">` | Kendo `<kendo-dropdownlist>` / `<mat-select>` / native `<select>` (same rules as `@Html.DropDownListFor`) |
| `<span asp-validation-for="Name">` | Inline `<div *ngIf="control.errors">` (same rules as `@Html.ValidationMessageFor`) |
| `<div asp-validation-summary="All">` | Form-level error summary component (same rules as `@Html.ValidationSummary()`) |
| `<a asp-action="Edit" asp-controller="X" asp-route-id="@id">` | `<a [routerLink]="['/x/edit', id]">` (same rules as `@Html.ActionLink`) |
| `<form asp-action="Create" asp-controller="X">` | `<form [formGroup] (ngSubmit)>` (same rules as `<form asp-action>`) |
| `<img asp-append-version="true">` | `<img src="assets/path">` — Angular CLI hashes assets at build time; remove `asp-append-version` |
| `<environment include="Development">` | Use `environment.ts` / `environment.prod.ts` to conditionally include dev-only scripts or config |
| `<partial name="_X" />` | Child component with `@Input` (same rules as `@Html.Partial`) |
| Kendo Tag Helpers | Kendo Angular components (if installed in destination) |
| Bing Maps SDK / `Microsoft.Maps` | **STRICT — Direct Bing Maps V8 SDK** via `bingmaps` types package. Use `Microsoft.Maps.Map` in `AfterViewInit` + `ElementRef`. API key read from `environment.ts` (placeholder until user adds key to `appsettings.json` post-migration). Do not substitute with any other map provider. |

### [ANGULAR ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any view):**
> - Update `environment.ts` / `environment.development.ts` with the Web API base URL if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the component structure, module pattern, and service pattern to follow for this feature
2. Create TypeScript model/interface matching the API DTO
3. Create Angular service using `HttpClient` — follow destination's existing service patterns (base URL config, error handling, interceptors)
4. Create components (list, detail, create/edit) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (lazy-loaded modules or standalone routes)
6. **Migrate ALL form validations (STRICT)** — For every form field in the Razor view, extract every `data-val-*` attribute, jQuery Unobtrusive rule, and custom JS validator. Create an equivalent Angular Reactive Forms validator for **each one** — `Validators.required`, `Validators.minLength`, `Validators.maxLength`, `Validators.min`, `Validators.max`, `Validators.pattern`, custom `ValidatorFn` for cross-field rules, custom `AsyncValidatorFn` for remote/async validations. Preserve **all custom error messages exactly**. Display validation errors inline next to each field, matching the same UX as the source MVC app (show on blur / on submit, same positioning). If the source uses `@Html.ValidationSummary()`, create an equivalent form-level error summary component.
7. For Kendo MVC controls — reference the **Phase 4 Kendo Angular mapping table** for the equivalent Angular component (only if Kendo migration was confirmed in Project Paths step 4)
8. **Bing Maps migration (STRICT — Direct Bing Maps V8 SDK only)** — If the source view uses Bing Maps (look for `Microsoft.Maps.Map`, Bing Maps `<script>` tags, or `@Html.Raw` blocks initializing Bing Maps), **migrate as-is from source to destination using the Bing Maps V8 SDK directly.** Do not substitute with Google Maps, Leaflet, or any other map provider.
   - **Install:** `npm install bingmaps` (TypeScript type definitions for Bing Maps V8). Add `/// <reference types="bingmaps" />` in a global `.d.ts` file or at the top of the component file.
   - **Script loading:** Add the Bing Maps control script to `index.html` (`<script src="https://www.bing.com/api/maps/mapcontrol?callback=bingMapsReady"></script>`) or load it dynamically via an injectable `BingMapsLoaderService` that appends the script tag and resolves a Promise when the callback fires.
   - **API key handling:** Add a placeholder entry `"BingMaps": { "ApiKey": "" }` in `appsettings.json` on the Web API side. In `environment.ts`, add `bingMapsKey: ''`. The user will fill in the actual Bing Maps API key post-migration. During migration, replicate the exact same map configuration from the source — just wire the key reference to `environment.bingMapsKey` (passed to the component via an `@Input` or injected config service).
   - **Component implementation:** In the Angular component, use `AfterViewInit` + `@ViewChild` with an `ElementRef` container `<div>`. Initialize the map: `new Microsoft.Maps.Map(this.mapContainer.nativeElement, { credentials: this.apiKey, center: new Microsoft.Maps.Location(lat, lng), zoom: zoomLevel, mapTypeId: Microsoft.Maps.MapTypeId.road })`. Migrate **all** map features from source:
     - **Pushpins:** `const pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, lng), { icon: iconUrl, title: title });` → `map.entities.push(pin);`
     - **Infoboxes:** `const infobox = new Microsoft.Maps.Infobox(location, { title, description, visible: false });` → `infobox.setMap(map);` → show on pushpin click via `Microsoft.Maps.Events.addHandler(pin, 'click', () => infobox.setOptions({ visible: true }))`
     - **Polylines:** `new Microsoft.Maps.Polyline([loc1, loc2, ...], { strokeColor, strokeThickness })` → `map.entities.push(polyline);`
     - **Polygons:** `new Microsoft.Maps.Polygon([loc1, loc2, ...], { fillColor, strokeColor, strokeThickness })` → `map.entities.push(polygon);`
     - **Event handlers:** `Microsoft.Maps.Events.addHandler(map, 'click', callback)` — replicate all source event handlers
   - **Cleanup:** Implement `OnDestroy` to call `map.dispose()` and remove event handlers.
   - Preserve **all** source Bing Maps functionality with exact feature parity — map type, zoom level, center coordinates, pushpin locations/icons, infobox content, polyline/polygon paths and styling, event handlers.
9. Use other third-party controls **only if already installed** in destination (Material, etc.) — do not install new UI libraries
10. **Migrate `@section Scripts { }` blocks** — If the Razor view has a `@section Scripts` block containing JavaScript (Kendo widget initialization, custom validation, page-specific logic), migrate all that logic into the Angular component's `ngOnInit` / `AfterViewInit` lifecycle hooks or directive logic. Do not discard page-specific JS.
11. **Migrate ViewComponents** — If the Razor view invokes `@await Component.InvokeAsync("ComponentName")` or `<vc:component-name>`, create a standalone Angular component for each ViewComponent. The Angular component should fetch its own data via an injected service (matching the ViewComponent's `InvokeAsync` logic) and render the same UI.
12. Migrate CSS/styles — use destination's existing styling approach. Check in order: Angular component styles (`.scss`/`.css` co-located) → global `styles.scss` → CSS Modules if configured

---

### [REACT ONLY] — Razor → React Mapping

| Razor | React |
|---|---|
| `_Layout.cshtml` | Root layout component + shared header/sidebar/footer |
| `@model ViewModel` | TypeScript interface |
| `@Html.TextBoxFor` | `<input>` controlled component — use Kendo React `<Input>` only if Kendo is installed in destination |
| `@Html.DropDownListFor` | Kendo `<DropDownList>` if Kendo installed, otherwise `react-select` if installed, otherwise native `<select>` |
| `@Html.ValidationMessageFor` | `{errors.fieldName && <span>{errors.fieldName.message}</span>}` via `react-hook-form` `formState.errors` |
| `<form asp-action>` | `<form onSubmit={handleSubmit(onSubmit)}>` |
| `@Html.Partial("_X", item)` | Child component with props |
| `@Html.ActionLink` | `<Link to="...">` from `react-router-dom` |
| `@if / @foreach` | `{condition && <JSX>}` / `{array.map(...)}` |
| `ViewBag.Title` | `document.title` assignment in `useEffect`. Use `react-helmet-async` only if already installed. |
| `TempData["Msg"]` | `react-toastify` (default). Use `sweetalert2` only if already installed and `react-toastify` is not. |
| `@Html.DisplayFor` | `{model.property}` JSX expression (read-only display) |
| `@Html.DisplayNameFor` | Label text — use `<label>` with hardcoded label matching source |
| `@Html.EditorFor` | `<input {...register('field')}>` (same as `TextBoxFor` unless source renders a custom editor template — replicate that template as a child component) |
| `@Html.HiddenFor` | `<input type="hidden" {...register('field')}>` |
| `@Html.RadioButtonFor` | `<input type="radio" {...register('field')}>` |
| `@Html.CheckBoxFor` | `<input type="checkbox" {...register('field')}>` (Kendo `<Checkbox>` if Kendo installed) |
| `@Html.TextAreaFor` | `<textarea {...register('field')}>` (Kendo `<TextArea>` if Kendo installed) |
| `@Html.LabelFor` | `<label htmlFor="fieldId">` with text matching source label |
| `@Html.PasswordFor` | `<input type="password" {...register('field')}>` |
| `@Html.ListBoxFor` | `<select multiple {...register('field')}>` (Kendo `<MultiSelect>` if Kendo installed) |
| `@Html.Raw(...)` | `<div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />` — only if source content is trusted; prefer safe rendering |
| `@Html.ValidationSummary()` | Form-level error summary component — collect all `formState.errors` and display as a list above the form (match source UX) |
| `ViewData["key"]` | Component state, props, or React Context for shared state |
| `@Url.Action("Action", "Controller")` | Build route path string — e.g., `'/controller/action'` or use `generatePath()` from `react-router-dom` |
| `@Url.Content("~/path")` | Asset path — use `/path` relative to `public/` or `import` for bundled assets |
| `@Html.AntiForgeryToken()` | Not needed (JWT) |
| **ASP.NET Core Tag Helpers** | **React equivalents (same as `@Html.*` counterparts above):** |
| `<input asp-for="Name">` | `<input {...register('name')}>` (same rules as `@Html.TextBoxFor`) |
| `<textarea asp-for="Bio">` | `<textarea {...register('bio')}>` (same rules as `@Html.TextAreaFor`) |
| `<label asp-for="Name">` | `<label htmlFor="fieldId">` with text matching source label (same as `@Html.LabelFor`) |
| `<select asp-for="Cat" asp-items="...">` | Kendo `<DropDownList>` / `react-select` / native `<select>` (same rules as `@Html.DropDownListFor`) |
| `<span asp-validation-for="Name">` | `{errors.fieldName && <span>{errors.fieldName.message}</span>}` (same rules as `@Html.ValidationMessageFor`) |
| `<div asp-validation-summary="All">` | Form-level error summary component (same rules as `@Html.ValidationSummary()`) |
| `<a asp-action="Edit" asp-controller="X" asp-route-id="@id">` | `<Link to={\`/x/edit/${id}\`}>` (same rules as `@Html.ActionLink`) |
| `<form asp-action="Create" asp-controller="X">` | `<form onSubmit={handleSubmit(onSubmit)}>` (same rules as `<form asp-action>`) |
| `<img asp-append-version="true">` | `<img src="/path">` — Vite/CRA hashes assets at build time; remove `asp-append-version` |
| `<environment include="Development">` | Use `.env.development` / `.env.production` to conditionally include dev-only scripts or config |
| `<partial name="_X" />` | Child component with props (same rules as `@Html.Partial`) |
| Kendo Tag Helpers | Kendo React components (if installed in destination) |
| Bing Maps SDK / `Microsoft.Maps` | **STRICT — Direct Bing Maps V8 SDK** via `bingmaps` types package. Use `Microsoft.Maps.Map` in `useEffect` + `useRef<HTMLDivElement>`. API key read from env config (placeholder until user adds key post-migration). Do not substitute with any other map provider. |

### [REACT ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any view):**
> - Update `.env` / `.env.development` with the Web API base URL (`VITE_API_URL` or `REACT_APP_API_URL`) if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the page/component structure, routing setup, and data-fetching pattern to follow for this feature
2. Create TypeScript interface matching the API DTO
3. Create API service / custom hook (`useQuery`, `useMutation`, or custom `useXxx` hook) — follow destination's existing data-fetching patterns; include error handling (catch API errors and display via toast or inline message)
4. Create page and child components (list, detail, create/edit form) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (`react-router-dom` v6 `<Route>`, nested routes, or file-based routing)
6. **Migrate ALL form validations (STRICT)** — For every form field in the Razor view, extract every `data-val-*` attribute, jQuery Unobtrusive rule, and custom JS validator. Create an equivalent `yup` schema rule (default; use `zod` only if already installed and `yup` is not) for **each one** — `.required()`, `.min()`, `.max()`, `.matches()`, `.oneOf()` for cross-field, `.test()` for custom/async. Preserve **all custom error messages exactly**. Display validation errors inline next to each field using `formState.errors`, matching the same UX as the source MVC app (show on blur / on submit, same positioning). If the source uses `@Html.ValidationSummary()`, create an equivalent form-level error summary component.
7. For Kendo MVC controls — reference the **Phase 4 Kendo React mapping table** for the equivalent React component (only if Kendo migration was confirmed in Project Paths step 4)
8. **Bing Maps migration (STRICT — Direct Bing Maps V8 SDK only)** — If the source view uses Bing Maps (look for `Microsoft.Maps.Map`, Bing Maps `<script>` tags, or `@Html.Raw` blocks initializing Bing Maps), **migrate as-is from source to destination using the Bing Maps V8 SDK directly.** Do not substitute with Google Maps, Leaflet, or any other map provider.
   - **Install:** `npm install bingmaps` (TypeScript type definitions for Bing Maps V8). Add `/// <reference types="bingmaps" />` in a global `.d.ts` file.
   - **Script loading:** Load the Bing Maps control script dynamically in a custom hook (`useBingMapsLoader`) or a `useEffect` — append `<script src="https://www.bing.com/api/maps/mapcontrol?callback=bingMapsReady"></script>` to document head and resolve via the callback. Clean up the script tag in the `useEffect` cleanup.
   - **API key handling:** Add a placeholder entry `VITE_BINGMAPS_KEY=` (Vite) or `REACT_APP_BINGMAPS_KEY=` (CRA) in `.env`. The user will fill in the actual Bing Maps API key post-migration. During migration, replicate the exact same map configuration from the source — just wire the key reference to `import.meta.env.VITE_BINGMAPS_KEY` (Vite) or `process.env.REACT_APP_BINGMAPS_KEY` (CRA), passed to the component via props or context.
   - **Component implementation:** Create a reusable `BingMap` component. Use `useRef<HTMLDivElement>(null)` for the map container. In `useEffect` (after script loaded), initialize: `new Microsoft.Maps.Map(ref.current, { credentials: apiKey, center: new Microsoft.Maps.Location(lat, lng), zoom: zoomLevel, mapTypeId: Microsoft.Maps.MapTypeId.road })`. Migrate **all** map features from source:
     - **Pushpins:** `const pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, lng), { icon: iconUrl, title });` → `map.entities.push(pin);`
     - **Infoboxes:** `const infobox = new Microsoft.Maps.Infobox(location, { title, description, visible: false });` → `infobox.setMap(map);` → show on pushpin click via `Microsoft.Maps.Events.addHandler(pin, 'click', () => infobox.setOptions({ visible: true }))`
     - **Polylines:** `new Microsoft.Maps.Polyline([loc1, loc2, ...], { strokeColor, strokeThickness })` → `map.entities.push(polyline);`
     - **Polygons:** `new Microsoft.Maps.Polygon([loc1, loc2, ...], { fillColor, strokeColor, strokeThickness })` → `map.entities.push(polygon);`
     - **Event handlers:** `Microsoft.Maps.Events.addHandler(map, 'click', callback)` — replicate all source event handlers
   - **Cleanup:** In the `useEffect` cleanup function, call `map.dispose()` and remove event handlers to prevent memory leaks.
   - Preserve **all** source Bing Maps functionality with exact feature parity — map type, zoom level, center coordinates, pushpin locations/icons, infobox content, polyline/polygon paths and styling, event handlers.
9. Use other third-party controls **only if already installed** in destination (MUI, Ant Design, etc.) — do not install new UI libraries
10. **Migrate `@section Scripts { }` blocks** — If the Razor view has a `@section Scripts` block containing JavaScript (Kendo widget initialization, custom validation, page-specific logic), migrate all that logic into the React component's `useEffect` hooks, event handlers, or custom hooks. Do not discard page-specific JS.
11. **Migrate ViewComponents** — If the Razor view invokes `@await Component.InvokeAsync("ComponentName")` or `<vc:component-name>`, create a standalone React component for each ViewComponent. The React component should fetch its own data via a custom hook or `useEffect` (matching the ViewComponent's `InvokeAsync` logic) and render the same UI.
12. Migrate CSS/styles — use destination's existing styling approach. Check in order: CSS Modules (if `.module.css` files exist) → Tailwind (if `tailwind.config` exists) → styled-components (if installed) → plain CSS files

---

### Static Assets & CSS Migration

> **STRICT REQUIREMENT:** Migrate the **entire CSS** from the source MVC project. Every stylesheet in `wwwroot/css/`, `Views/Shared/`, bundled CSS, and inline `<style>` blocks in Razor views must be accounted for. The destination frontend must reproduce the **same visual design, layout, spacing, colors, typography, and responsive behavior** as the source application. Do not discard, simplify, or "modernize" styles — preserve full visual fidelity.

**CSS Migration Steps:**

1. **Inventory all CSS sources** — Collect every CSS file from `wwwroot/css/`, `wwwroot/lib/`, `bundleconfig.json` / `_BundleConfig.cs`, `<link>` references in `_Layout.cshtml`, inline `<style>` blocks in Razor views, and any SCSS/LESS source files.
2. **Map CSS to destination structure** — Move all stylesheets into the destination project's styling location. Maintain the same file organization (e.g., if source has `site.css`, `custom.css`, `page-specific.css`, create equivalent files or sections in the destination).
3. **Preserve all class names and selectors** — Keep the same CSS class names used in the source so that migrated HTML/components render identically. Do not rename classes unless the destination project enforces scoped styles (CSS Modules, Angular `ViewEncapsulation`), in which case map every class explicitly.
4. **Migrate page-specific and component-specific styles** — Any CSS scoped to a specific Razor view or partial must be co-located with the equivalent frontend component (Angular component styles / React CSS Module or styled-component).
5. **Migrate media queries and responsive breakpoints** — Preserve all `@media` rules exactly as defined in the source. Do not replace with a different breakpoint system unless the user explicitly requests it.
6. **Migrate CSS variables and theming** — If the source uses CSS custom properties (`--var`), SCSS/LESS variables, or Kendo theme variables, replicate them in the destination's theming setup.
7. **Migrate vendor/third-party CSS** — If the source includes Bootstrap, Kendo CSS theme, Font Awesome, or other library stylesheets, ensure the same versions or equivalent styles are included in the destination project.
8. **Remove jQuery and JS-only assets** — Remove jQuery, jQuery plugins, and other JS files that are replaced by framework equivalents. Do **not** remove any CSS that was loaded alongside those libraries.
9. **Migrate JavaScript bundles** — For each JS bundle in `bundleconfig.json` / `_BundleConfig.cs`, identify the purpose of every input file. jQuery and jQuery plugin files are removed (replaced by framework equivalents). Custom JS files containing business logic, page initialization, or utility functions must be migrated into the appropriate component/hook/service in the destination frontend. Do not silently drop any JS file without confirming its logic is covered by the migrated components.
10. **Visual verification** — After migration, every page/component should visually match the source MVC application. Flag any CSS that could not be migrated 1:1 and note the deviation.

Move `wwwroot/images/` → destination's assets location. Use destination's existing asset pipeline for images and static files.

---

## Phase 4: Kendo Component Reference (Used During Phase 3)

> **This is a reference section, not a standalone execution phase.** Phase 3 Per-View Steps point here whenever a Kendo MVC control needs to be replaced. Only apply if Kendo migration was confirmed in Project Paths step 4.

### [ANGULAR ONLY] — Kendo Angular Reference

Apply this phase only if Kendo migration was confirmed and packages were set up in the Project Paths section (step 4). By this point, `@progress/kendo-angular-*` packages are already installed in the destination project.

| MVC Kendo | Angular Kendo |
|---|---|
| `Html.Kendo().Grid<T>()` | `<kendo-grid>` |
| `Html.Kendo().DropDownList()` | `<kendo-dropdownlist>` |
| `Html.Kendo().DatePicker()` | `<kendo-datepicker>` |
| `Html.Kendo().NumericTextBox()` | `<kendo-numerictextbox>` |
| `Html.Kendo().Chart()` | `<kendo-chart>` |
| `Html.Kendo().Upload()` | `<kendo-upload>` |
| `Html.Kendo().Window()` | `<kendo-dialog>` (default). Use `DialogService` only if the destination project already uses programmatic dialog opening. |
| `Html.Kendo().TabStrip()` | `<kendo-tabstrip>` |
| `Html.Kendo().ExpansionPanel()` | `<kendo-expansionpanel>` from `@progress/kendo-angular-layout` |
| `Html.Kendo().TreeView()` | `<kendo-treeview>` |
| `Html.Kendo().Editor()` | `<kendo-editor>` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side.

---

### [REACT ONLY] — Kendo React Reference

Apply this phase only if Kendo migration was confirmed and packages were set up in the Project Paths section (step 4). By this point, `@progress/kendo-react-*` packages are already installed in the destination project.

| MVC Kendo | React Kendo |
|---|---|
| `Html.Kendo().Grid<T>()` | `<Grid>` from `@progress/kendo-react-grid` |
| `Html.Kendo().DropDownList()` | `<DropDownList>` from `@progress/kendo-react-dropdowns` |
| `Html.Kendo().DatePicker()` | `<DatePicker>` from `@progress/kendo-react-dateinputs` |
| `Html.Kendo().NumericTextBox()` | `<NumericTextBox>` from `@progress/kendo-react-inputs` |
| `Html.Kendo().Chart()` | `<Chart>` from `@progress/kendo-react-charts` |
| `Html.Kendo().Upload()` | `<Upload>` from `@progress/kendo-react-upload` |
| `Html.Kendo().Window()` | `<Dialog>` from `@progress/kendo-react-dialogs` |
| `Html.Kendo().TabStrip()` | `<TabStrip>` from `@progress/kendo-react-layout` |
| `Html.Kendo().ExpansionPanel()` | `<ExpansionPanel>` from `@progress/kendo-react-layout` |
| `Html.Kendo().TreeView()` | `<TreeView>` from `@progress/kendo-react-treeview` |
| `Html.Kendo().Editor()` | `<Editor>` from `@progress/kendo-react-editor` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side (same as Angular).

---

## Phase 5: Per-Controller Checklist

> **Complete the one-time setup below once before starting any controller migration. Then use the per-controller checklist for each controller.**

**One-Time Setup — [ANGULAR ONLY]:**
- [ ] `environment.ts` / `environment.development.ts` / `environment.staging.ts` / `environment.prod.ts` API base URLs set for all environments
- [ ] Auth pages (login/register) migrated, JWT storage in place
- [ ] `HttpInterceptor` attaching `Authorization: Bearer` header
- [ ] `HttpInterceptor` handling `400` ProblemDetails — maps server validation errors to form controls via `setErrors()`
- [ ] `HttpInterceptor` handling `401`, `403`, `5xx` — redirect to error pages or display notification
- [ ] `CanActivateFn` route guard for protected routes
- [ ] Custom error page components (404, 500, AccessDenied) with wildcard route
- [ ] SignalR Angular service created using `@microsoft/signalr` (if applicable)
- [ ] Localization setup — `@ngx-translate/core` (default) or `@angular/localize` (if project uses it) with translation JSON files (if source uses i18n)
- [ ] MVC Areas mapped to lazy-loaded feature modules / standalone route groups (if applicable)
- [ ] Bing Maps one-time setup — `npm install bingmaps`, `/// <reference types="bingmaps" />` in global `.d.ts`, Bing Maps script loaded in `index.html` or via `BingMapsLoaderService`, `bingMapsKey: ''` placeholder in `environment.ts`, `"BingMaps": { "ApiKey": "" }` in `appsettings.json` (if source uses Bing Maps)

**One-Time Setup — [REACT ONLY]:**
- [ ] `.env.local` / `.env.development` / `.env.staging` / `.env.production` API base URLs set for all environments
- [ ] Auth pages (login/register) migrated, JWT storage in place
- [ ] Axios interceptor (or equivalent) attaching `Authorization: Bearer` header
- [ ] Axios interceptor handling `400` ProblemDetails — maps server validation errors to form fields via `setError()`
- [ ] Axios interceptor handling `401`, `403`, `5xx` — redirect to error pages or display notification
- [ ] Protected route component for guarded routes
- [ ] Custom error page components (404, 500, AccessDenied) with catch-all route
- [ ] SignalR React hook created using `@microsoft/signalr` (if applicable)
- [ ] Localization setup — `react-i18next` (default) or `react-intl` (only if already installed and react-i18next is not) with translation JSON files (if source uses i18n)
- [ ] MVC Areas mapped to nested route groups (if applicable)
- [ ] Bing Maps one-time setup — `npm install bingmaps`, `/// <reference types="bingmaps" />` in global `.d.ts`, Bing Maps loader hook/utility created, `VITE_BINGMAPS_KEY=` or `REACT_APP_BINGMAPS_KEY=` placeholder in `.env`, `"BingMaps": { "ApiKey": "" }` in `appsettings.json` (if source uses Bing Maps)

---

**Per-Controller — Backend (both frameworks):**
- [ ] API Controller (follow destination conventions)
- [ ] Services + Interfaces (follow destination service layer)
- [ ] DTOs + AutoMapper profile (follow destination DTO patterns)
- [ ] All server-side validations migrated (data annotations, FluentValidation, custom attributes) — return `ValidationProblemDetails` on failure
- [ ] Custom middleware/filters migrated
- [ ] Entity models, EF configurations, seed data for this controller's domain entities migrated into destination data layer (DbContext class itself is a one-time setup — see Phase 2 "DbContext & EF Core Migration")
- [ ] EF Core interceptors, query filters migrated
- [ ] Migrations regenerated, connection strings updated
- [ ] Register services + DbContext in DI
- [ ] File upload endpoints migrated (`IFormFile` / `[FromForm]`) with validation (if applicable)
- [ ] Localized validation messages and resource strings migrated (if applicable)
- [ ] SignalR hub verified in Web API + CORS credentials allowed (if applicable)
- [ ] Background jobs migrated and registered (if applicable)
- [ ] `appsettings.*.json` updated for all environments (dev, staging, prod)

**Per-Controller — Frontend [ANGULAR ONLY]:**
- [ ] TypeScript models/interfaces
- [ ] Angular Service with `HttpClient` (follow destination service pattern)
- [ ] List, Detail, Create/Edit components (follow destination component pattern)
- [ ] Feature routing — lazy-loaded modules or standalone routes
- [ ] **ALL client-side validations migrated** — every `data-val-*` rule, custom JS validator → Reactive Forms `ValidatorFn` / `AsyncValidatorFn` with exact error messages preserved
- [ ] Validation error display matches source UX (inline errors, validation summary if applicable)
- [ ] **API ProblemDetails errors displayed inline** — server-side 400 validation errors mapped to form controls via `setErrors()`
- [ ] File upload component migrated (if applicable)
- [ ] Localized UI strings migrated to translation files (if applicable)
- [ ] Kendo Angular controls replaced using Phase 4 reference table (if confirmed in Project Paths step 4)
- [ ] Bing Maps component migrated using Direct Bing Maps V8 SDK — all pushpins, infoboxes, polylines, polygons, event handlers replicated with exact feature parity (if source view uses Bing Maps)
- [ ] SignalR Angular service wired into component (if applicable)
- [ ] Migrate CSS/SCSS styles
- [ ] E2E test full flow

**Per-Controller — Frontend [REACT ONLY]:**
- [ ] TypeScript interfaces
- [ ] API service / custom hook (axios, React Query, etc. — follow destination pattern)
- [ ] Page and child components (list, detail, create/edit form)
- [ ] Feature routing — `react-router-dom` routes (follow destination routing pattern)
- [ ] **ALL client-side validations migrated** — every `data-val-*` rule, custom JS validator → `yup` schema rules (or `zod` if already installed) with exact error messages preserved
- [ ] Validation error display matches source UX (inline errors, validation summary if applicable)
- [ ] **API ProblemDetails errors displayed inline** — server-side 400 validation errors mapped to form fields via `setError()`
- [ ] File upload component migrated (if applicable)
- [ ] Localized UI strings migrated to translation files (if applicable)
- [ ] Kendo React controls replaced using Phase 4 reference table (if confirmed in Project Paths step 4)
- [ ] Bing Maps component migrated using Direct Bing Maps V8 SDK — all pushpins, infoboxes, polylines, polygons, event handlers replicated with exact feature parity (if source view uses Bing Maps)
- [ ] SignalR React hook wired into component (if applicable)
- [ ] Migrate CSS/styles — use destination's existing styling approach (check in order: CSS Modules → Tailwind → styled-components → plain CSS)
- [ ] E2E test full flow

**Order:** Core/Auth first → then remaining controllers in **alphabetical order** → Complex features last (SignalR, file uploads). Within each controller: Index/List → Details → Create → Edit → Delete → remaining views alphabetically.

**After ALL controllers are fully migrated (backend + frontend):**
- Mark Phase 2, Phase 3, and Phase 5 as `[x] COMPLETED` in `MIGRATION_PROGRESS.md`
- Update "Last Updated" timestamp
- Print final summary: total controllers migrated, total files created, any skipped items
- **Do NOT delete `MIGRATION_PROGRESS.md`** — keep it as a migration audit trail. The user may delete it manually when satisfied.

---

## Quick Reference: Key Transformations

**Backend (both frameworks):**

| MVC | Web API |
|---|---|
| `Controller : Controller` → Views | `ControllerBase` → JSON |
| ViewModels | DTOs (API) |
| `[ValidateAntiForgeryToken]` | JWT Bearer |
| `ModelState` | `[ApiController]` auto-validation |
| `RedirectToAction` | `CreatedAtAction` / `NoContent` / status codes |
| Custom Filters | API Filters / Middleware |
| FluentValidation / DataAnnotations | API DTOs + FluentValidation |
| AutoMapper profiles | Updated AutoMapper profiles for DTOs |
| DbContext / EF Core entities | Migrated into destination's data layer |
| EF Core configurations / seed data | `IEntityTypeConfiguration<T>` / `HasData()` in destination structure |
| EF Core interceptors / query filters | Destination middleware / DbContext overrides |
| SignalR hubs | Kept in Web API; frontend service/hook via `@microsoft/signalr` |
| Background jobs | Migrated into Web API — Hangfire / `IHostedService` |

**Frontend — [ANGULAR ONLY]:**

| MVC | Angular |
|---|---|
| `.cshtml` Razor Views | Angular Components (`.ts` + `.html`) |
| ViewModels | TS Interfaces |
| `@Html` helpers | Angular directives / pipes / Kendo Angular |
| `[ValidateAntiForgeryToken]` | `HttpInterceptor` (JWT bearer header) |
| `ModelState` | Angular Reactive Forms + `ValidatorFn` |
| `RedirectToAction` | `router.navigate()` |
| `TempData` / `ViewBag` | `ngx-toastr` for notifications, Angular services for shared state |
| Partial Views | Child components (`@Input`/`@Output`) |
| ViewComponents | Standalone Angular components (self-contained, with own data fetching via service) |
| `_Layout.cshtml` | App shell + shared layout components |
| jQuery / vanilla JS | RxJS, Angular directives, Angular pipes |
| Session state | JWT claims in `HttpInterceptor`, or NgRx if already installed in destination |

**Frontend — [REACT ONLY]:**

| MVC | React |
|---|---|
| `.cshtml` Razor Views | React Components (`.tsx`) |
| ViewModels | TS Interfaces |
| `@Html` helpers | React components / utility functions |
| `[ValidateAntiForgeryToken]` | Axios interceptor (JWT bearer header) |
| `ModelState` | `react-hook-form` + `yup` (default; `zod` only if already installed) |
| `RedirectToAction` | `useNavigate()` from `react-router-dom` |
| `TempData` / `ViewBag` | `react-toastify` for notifications, React Context for shared state |
| Partial Views | Child components (props) |
| ViewComponents | Standalone React components (self-contained, with own data fetching via custom hook) |
| `_Layout.cshtml` | Root layout component |
| jQuery / vanilla JS | Custom hooks, utility functions |
| Session state | JWT claims in axios interceptor, or Zustand/Redux if already installed in destination |