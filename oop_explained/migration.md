# ASP.NET Core MVC → Angular / React + Web API Migration Plan

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
> - **Frontend:** HTTP client setup (Angular `HttpClientModule` / React `axios` or `fetch`), environment/config file with API base URL placeholder
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

- **All server-side validations** — Data annotations, FluentValidation rules, custom `IValidatableObject` implementations, action filter validations → migrate to API DTOs (server-side)
- **All client-side validations:**
  > **[ANGULAR ONLY]** jQuery Unobtrusive Validation, custom JS validators → Angular Reactive Forms validators (built-in + custom `ValidatorFn` / `AsyncValidatorFn`)
  > **[REACT ONLY]** jQuery Unobtrusive Validation, custom JS validators → `react-hook-form` validators with `yup` or `zod` schema (or built-in validation rules matching what's installed)
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

Inventory all: Controllers (actions, routes, `[Authorize]`), Razor Views (layouts, partials, tag helpers), View Models, EF Core entities/DbContext, Services, Static assets, Third-party libs (Kendo etc.), Middleware/Filters, Custom Validations, AutoMapper profiles, SignalR hubs, Background jobs.

**Before proceeding to Phase 2, produce an inventory summary** listing:
- All controllers and their action count
- All Razor views grouped by controller
- All EF Core entities and DbContext classes
- All third-party libraries detected
- All SignalR hubs (if any)
- All background jobs (if any)
- Any custom middleware, filters, or validation attributes

Present this summary to the user and wait for confirmation before beginning Phase 2.

**Library Mapping:**

> **[ANGULAR ONLY]**

| MVC Library | Angular Equivalent |
|---|---|
| Kendo UI / Telerik | `@progress/kendo-angular-*` |
| Bootstrap | `ngx-bootstrap` / `@ng-bootstrap/ng-bootstrap` |
| jQuery Validation | Angular Reactive Forms |
| DataTables | Kendo Grid / Material Table |
| Select2 | Kendo DropDownList / Material Autocomplete |
| Chart.js/Highcharts | Kendo Charts / `ngx-charts` |
| Toastr / SweetAlert | `ngx-toastr` / `sweetalert2` |

---

> **[REACT ONLY]**

| MVC Library | React Equivalent |
|---|---|
| Kendo UI / Telerik | `@progress/kendo-react-*` |
| Bootstrap | `react-bootstrap` / `reactstrap` |
| jQuery Validation | `react-hook-form` + `yup` / `zod` |
| DataTables | Kendo Grid / MUI DataGrid / `@tanstack/react-table` |
| Select2 | `react-select` / Kendo DropDownList |
| Chart.js/Highcharts | Kendo Charts / `recharts` / `@nivo/core` |
| Toastr / SweetAlert | `react-toastify` / `sweetalert2` |

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

---

## Phase 3: Frontend — Razor Views → [SELECTED_FRAMEWORK]

---

### Auth UI Migration (both frameworks)

> **Migrate auth pages first, before any other views.** Route guards and protected routes depend on the auth flow being in place.

If the source MVC app has login, register, or account management pages, migrate them as the first feature in Phase 3:

> **[ANGULAR ONLY]**
> - Create a login/register component with a Reactive Form
> - On successful login, store the JWT token (`localStorage` or `sessionStorage`) and redirect
> - Create an `HttpInterceptor` that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present in the destination project)
> - Create an `CanActivateFn` route guard that checks for a valid token and redirects to login if missing

> **[REACT ONLY]**
> - Create login/register page components with `react-hook-form`
> - On successful login, store the JWT token (`localStorage` or `sessionStorage` or a context/state store) and redirect via `useNavigate()`
> - Configure an axios interceptor (or equivalent) that attaches the `Authorization: Bearer <token>` header to every outgoing API request (if not already present)
> - Create a protected route component that checks for a valid token and redirects to login if missing

---

### [ANGULAR ONLY] — Razor → Angular Mapping

| Razor | Angular |
|---|---|
| `_Layout.cshtml` | App shell + shared header/sidebar/footer (match destination layout) |
| `@model ViewModel` | TypeScript interface |
| `@Html.TextBoxFor` | `<input formControlName>` / Kendo textbox (use what's installed) |
| `@Html.DropDownListFor` | Kendo dropdownlist / Material select (use what's installed) |
| `@Html.ValidationMessageFor` | Angular form error display (match destination pattern) |
| `<form asp-action>` | `<form [formGroup] (ngSubmit)>` |
| `@Html.Partial("_X", item)` | Child component with `@Input` |
| `@Html.ActionLink` | `<a [routerLink]>` |
| `@if / @foreach` | `*ngIf`/`*ngFor` or `@if`/`@for` (match destination's Angular version) |
| `ViewBag.Title` | Title service |
| `TempData["Msg"]` | Notification service (use what's installed in destination) |
| `@Html.AntiForgeryToken()` | Not needed (JWT) |
| Kendo Tag Helpers | Kendo Angular components (if installed in destination) |

### [ANGULAR ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any view):**
> - Update `environment.ts` / `environment.development.ts` with the Web API base URL if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the component structure, module pattern, and service pattern to follow for this feature
2. Create TypeScript model/interface matching the API DTO
3. Create Angular service using `HttpClient` — follow destination's existing service patterns (base URL config, error handling, interceptors)
4. Create components (list, detail, create/edit) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (lazy-loaded modules or standalone routes)
6. Migrate all form validations — match destination's form validation approach (reactive forms, template forms, or existing custom validators using `ValidatorFn` / `AsyncValidatorFn`)
7. For Kendo MVC controls — reference the **Phase 4 Kendo Angular mapping table** for the equivalent Angular component (only if Kendo migration was confirmed in Project Paths step 4)
8. Use other third-party controls **only if already installed** in destination (Material, etc.)
9. Migrate CSS/styles into destination's styling approach (SCSS, CSS modules, global styles)

---

### [REACT ONLY] — Razor → React Mapping

| Razor | React |
|---|---|
| `_Layout.cshtml` | Root layout component + shared header/sidebar/footer |
| `@model ViewModel` | TypeScript interface |
| `@Html.TextBoxFor` | `<input>` controlled component / Kendo React textbox (use what's installed) |
| `@Html.DropDownListFor` | `<select>` / `react-select` / Kendo DropDownList (use what's installed) |
| `@Html.ValidationMessageFor` | Form error display via `react-hook-form` `errors` object |
| `<form asp-action>` | `<form onSubmit={handleSubmit(onSubmit)}>` |
| `@Html.Partial("_X", item)` | Child component with props |
| `@Html.ActionLink` | `<Link to="...">` from `react-router-dom` |
| `@if / @foreach` | `{condition && <JSX>}` / `{array.map(...)}` |
| `ViewBag.Title` | `document.title` / `react-helmet-async` |
| `TempData["Msg"]` | Toast notification (use what's installed — `react-toastify`, etc.) |
| `@Html.AntiForgeryToken()` | Not needed (JWT) |
| Kendo Tag Helpers | Kendo React components (if installed in destination) |

### [REACT ONLY] — Per-View Steps

> **One-time setup (do this once before migrating any view):**
> - Update `.env` / `.env.development` with the Web API base URL (`VITE_API_URL` or `REACT_APP_API_URL`) if not already set.

1. **Refer to the Pre-Migration destination analysis** — confirm the page/component structure, routing setup, and data-fetching pattern to follow for this feature
2. Create TypeScript interface matching the API DTO
3. Create API service / custom hook (`useQuery`, `useMutation`, or custom `useXxx` hook) — follow destination's existing data-fetching patterns; include error handling (catch API errors and display via toast or inline message)
4. Create page and child components (list, detail, create/edit form) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (`react-router-dom` v6 `<Route>`, nested routes, or file-based routing)
6. Migrate all form validations — use `react-hook-form` with `yup` or `zod` resolver, or the existing validation library in the destination project
7. For Kendo MVC controls — reference the **Phase 4 Kendo React mapping table** for the equivalent React component (only if Kendo migration was confirmed in Project Paths step 4)
8. Use other third-party controls **only if already installed** in destination (MUI, Ant Design, etc.)
9. Migrate CSS/styles into destination's styling approach (CSS Modules, styled-components, Tailwind, global styles)

---

### Static Assets

Move `wwwroot/css/` → destination's styles location, `wwwroot/images/` → destination's assets location. Remove jQuery. Use destination's existing asset pipeline.

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
| `Html.Kendo().Window()` | `<kendo-dialog>` / `DialogService` |
| `Html.Kendo().TabStrip()` | `<kendo-tabstrip>` |
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
| `Html.Kendo().TreeView()` | `<TreeView>` from `@progress/kendo-react-treeview` |
| `Html.Kendo().Editor()` | `<Editor>` from `@progress/kendo-react-editor` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side (same as Angular).

---

## Phase 5: Per-Controller Checklist

> **Complete the one-time setup below once before starting any controller migration. Then use the per-controller checklist for each controller.**

**One-Time Setup — [ANGULAR ONLY]:**
- [ ] `environment.ts` / `environment.development.ts` API base URL set
- [ ] Auth pages (login/register) migrated, JWT storage in place
- [ ] `HttpInterceptor` attaching `Authorization: Bearer` header
- [ ] `CanActivateFn` route guard for protected routes
- [ ] SignalR Angular service created using `@microsoft/signalr` (if applicable)

**One-Time Setup — [REACT ONLY]:**
- [ ] `.env` / `.env.development` API base URL set (`VITE_API_URL` / `REACT_APP_API_URL`)
- [ ] Auth pages (login/register) migrated, JWT storage in place
- [ ] Axios interceptor (or equivalent) attaching `Authorization: Bearer` header
- [ ] Protected route component for guarded routes
- [ ] SignalR React hook created using `@microsoft/signalr` (if applicable)

---

**Per-Controller — Backend (both frameworks):**
- [ ] API Controller (follow destination conventions)
- [ ] Services + Interfaces (follow destination service layer)
- [ ] DTOs + AutoMapper profile (follow destination DTO patterns)
- [ ] All server-side validations migrated (data annotations, FluentValidation, custom attributes)
- [ ] Custom middleware/filters migrated
- [ ] DbContext, entities, configurations, seed data migrated
- [ ] EF Core interceptors, query filters migrated
- [ ] Migrations regenerated, connection strings updated
- [ ] Register services + DbContext in DI
- [ ] SignalR hub verified in Web API + CORS credentials allowed (if applicable)
- [ ] Background jobs migrated and registered (if applicable)

**Per-Controller — Frontend [ANGULAR ONLY]:**
- [ ] TypeScript models/interfaces
- [ ] Angular Service with `HttpClient` (follow destination service pattern)
- [ ] List, Detail, Create/Edit components (follow destination component pattern)
- [ ] Feature routing — lazy-loaded modules or standalone routes
- [ ] Reactive Form validation — `ValidatorFn` / `AsyncValidatorFn`
- [ ] Kendo Angular controls replaced using Phase 4 reference table (if confirmed in Project Paths step 4)
- [ ] Migrate CSS/SCSS styles
- [ ] E2E test full flow

**Per-Controller — Frontend [REACT ONLY]:**
- [ ] TypeScript interfaces
- [ ] API service / custom hook (axios, React Query, etc. — follow destination pattern)
- [ ] Page and child components (list, detail, create/edit form)
- [ ] Feature routing — `react-router-dom` routes (follow destination routing pattern)
- [ ] Form validation — `react-hook-form` + `yup`/`zod` (follow destination pattern)
- [ ] Kendo React controls replaced using Phase 4 reference table (if confirmed in Project Paths step 4)
- [ ] SignalR React hook wired into component (if applicable)
- [ ] Migrate CSS/styles (CSS Modules, Tailwind, styled-components)
- [ ] E2E test full flow

**Order:** Core/Auth first → Simplest CRUD feature → Remaining features → Complex features (SignalR, file uploads)

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
| `TempData` / `ViewBag` | Services / `ngx-toastr` |
| Partial Views | Child components (`@Input`/`@Output`) |
| `_Layout.cshtml` | App shell + shared layout components |
| jQuery / vanilla JS | RxJS, directives, pipes |
| Session state | JWT claims / NgRx / service state |

**Frontend — [REACT ONLY]:**

| MVC | React |
|---|---|
| `.cshtml` Razor Views | React Components (`.tsx`) |
| ViewModels | TS Interfaces |
| `@Html` helpers | React components / utility functions |
| `[ValidateAntiForgeryToken]` | Axios interceptor (JWT bearer header) |
| `ModelState` | `react-hook-form` + `yup`/`zod` |
| `RedirectToAction` | `useNavigate()` from `react-router-dom` |
| `TempData` / `ViewBag` | `react-toastify` / context / state |
| Partial Views | Child components (props) |
| `_Layout.cshtml` | Root layout component |
| jQuery / vanilla JS | Custom hooks, utility functions |
| Session state | JWT claims / Zustand / Redux / Context |