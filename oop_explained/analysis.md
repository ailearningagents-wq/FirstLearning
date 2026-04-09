# Pre-Migration Analysis Prompt
# Usage: Run this prompt FIRST. It inspects both projects and writes migration-phase.md.
# After this completes, run migration-phase.md to execute the actual migration.

---

## Purpose

This prompt performs a **deep, read-only analysis** of the source ASP.NET Core MVC project and the destination projects (Frontend + Web API). It resolves every migration decision upfront — framework choices, naming conventions, library selections, controller order, validation rules — and writes a concrete, project-specific migration plan to **`migration-phase.md`** in this workspace.

**No files in the source or destination projects are modified during this analysis.**

---

## Prerequisites — Load Reference Document

**Before starting any step, read `migration.md` in this workspace in full.** That file contains:
- The master library priority tables used for Step 4.1 decision resolution
- The Kendo Angular / Kendo React component reference tables (referenced during Step 4.1)
- Default library selection order for all frameworks and features

Do not proceed to Step 1 until `migration.md` has been fully read and its defaults are loaded into context.

---

## Determinism Rules (apply throughout this analysis)

When multiple options exist:
1. **Use what is already installed** in the destination project first.
2. **If nothing is installed**, default to the first option listed in `migration.md`.
3. **Never introduce a library** not already present and not the first-listed default.

---

## Step 1: Collect Project Configuration

Ask the user the following questions **one at a time**. Wait for each answer before proceeding to the next.

### 1.1 — Frontend Framework

Ask:
> **"Which frontend framework are you migrating to? (Angular / React)"**

Store as `[SELECTED_FRAMEWORK]`. All analysis and generated plan will be scoped to this framework only.

---

### 1.2 — Source Project Path

Ask:
> **"Please provide the full path to the Source ASP.NET Core MVC project:"**

Validate:
- Path exists on disk
- Contains at least one `.csproj` file
- Contains a `Controllers/` folder or `.cs` files with `Controller` suffix

If validation fails, report the issue and ask again.

---

### 1.3 — Destination Frontend Path

**[ANGULAR ONLY]** Ask:
> **"Please provide the full path to the Destination Angular project:"**

Validate: path exists, contains `package.json` and `angular.json`.

**[REACT ONLY]** Ask:
> **"Please provide the full path to the Destination React project:"**

Validate: path exists, contains `package.json` and one of `vite.config.ts`, `vite.config.js`, or `react-scripts` in dependencies.

---

### 1.4 — Destination Web API Path

Ask:
> **"Please provide the full path to the Destination C# Web API project:"**

Validate: path exists, contains a `.csproj` file and a `Controllers/` folder or `Program.cs`.

---

### 1.5 — Kendo UI

Ask:
> **"Does the source MVC application use Kendo UI? (yes/no)"**

If **yes**:
- Ask: **"Which version of Kendo UI is used in the source? (check `bower.json`, `package.json`, or Kendo CDN script version):"**
- Check destination `package.json` for `@progress/kendo-angular-*` (Angular) or `@progress/kendo-react-*` (React).
- Record: installed version if found, or "not installed — will use default".

If **no**: Record Kendo = false. Phase 4 of the migration plan will be skipped.

---

## Step 2: Analyze Source MVC Project

Perform a **complete, recursive scan** of the source project directory. Do not skip any folder. Record findings in structured sections below. This data feeds directly into `migration-phase.md`.

### 2.0 — Referenced Class Library Projects (Scan First)

Before scanning the MVC project itself, check for a `.sln` file in the source directory or its parent folder. If found:
- Parse all `<ProjectReference Include="...">` entries in the MVC `.csproj`
- List every referenced project path (e.g., `../MyApp.Domain/`, `../MyApp.Infrastructure/`, `../MyApp.Application/`)
- **Include those project directories in all scans in Sections 2.1–2.15** — entities, services, repositories, validators, and AutoMapper profiles frequently live in sibling class library projects, not the MVC project itself
- If no `.sln` is found, record "Single-project solution — no referenced projects" and proceed

Record: list of all project paths that will be included in the full scan.

---

### 2.1 — Controllers

Scan all `.cs` files for classes inheriting `Controller` or `ControllerBase`.

For each controller, record:
- Controller name (class name)
- All action method names, HTTP verbs, and route attributes
- `[Authorize]` attributes (roles, policies) on the controller and each action
- Whether it is in an MVC Area (note Area name)
- Number of views associated (count `.cshtml` files in `Views/{ControllerName}/`)
- Any `IFormFile` parameters (file upload)
- Any `[OutputCache]` / `[ResponseCache]` attributes

Sort the recorded list: **Auth/Account controllers first**, then remaining controllers alphabetically.

---

### 2.2 — Razor Views

Scan all `.cshtml` files under `Views/`.

For each view, record:
- Controller it belongs to
- View name and type (Index/List, Details, Create, Edit, Delete, or other)
- All `@Html.*` helpers and ASP.NET Core Tag Helpers used
- All `data-val-*` attributes found on `<input>`, `<select>`, `<textarea>` elements — list each attribute and its value per field
- All `@Html.ValidationMessageFor` / `<span asp-validation-for>` — list each validated field
- `@Html.ValidationSummary()` or `<div asp-validation-summary>` presence
- Kendo Tag Helpers found (if Kendo = yes)
- Bing Maps usage — look for `Microsoft.Maps`, `bing.com/api/maps`, `mapcontrol`
- `@await Component.InvokeAsync(...)` / `<vc:...>` — list ViewComponents invoked
- `@section Scripts { }` blocks — summarize the JS contained (don't duplicate the full source, just describe: "Kendo Grid init", "custom validator for X", etc.)
- `@Html.Partial(...)` / `<partial name="..." />` calls — list partial names

Also scan:
- `_Layout.cshtml` — note the layout structure: nav, sidebar, footer, sections, CSS links, JS bundles
- `_ViewImports.cshtml` — list all `@using`, `@addTagHelper`, `@inject`
- `_ViewStart.cshtml` — note default layout
- `Views/Shared/` — list all shared partials, error pages (404, 500, AccessDenied, etc.)

---

### 2.3 — ViewModels

Scan all classes used as `@model` in views or as action parameters.

For each ViewModel, record:
- Class name and namespace
- All properties with their types
- All data annotation attributes per property (`[Required]`, `[StringLength]`, `[Range]`, `[RegularExpression]`, `[Compare]`, `[EmailAddress]`, etc.)
- Any `IValidatableObject.Validate()` implementations
- Any custom `ValidationAttribute` subclasses used

---

### 2.4 — EF Core / DbContext

Scan for classes inheriting `DbContext` or `IdentityDbContext`.

For each DbContext, record:
- Class name and namespace
- All `DbSet<T>` properties and their entity types
- All entity configuration files (`IEntityTypeConfiguration<T>` or `OnModelCreating` Fluent API setup)
- Global query filters (`HasQueryFilter(...)`)
- Seed data (`HasData(...)`)
- EF Core interceptors (`SaveChangesInterceptor`, `DbCommandInterceptor`)
- `connectionStrings` entry name used in config

---

### 2.5 — Services and Repositories

Scan for service interfaces (`IXxxService`) and implementations.

For each service, record:
- Interface name and implementation name
- Methods (name, parameters, return type)
- Which controllers consume it
- Any existing AutoMapper profiles (`Profile` subclasses) — list each `CreateMap<Source, Dest>()` mapping

---

### 2.6 — Custom Validations

Scan for:
- All `ValidationAttribute` subclasses — list class names and what they validate
- All FluentValidation validators (`AbstractValidator<T>` subclasses) — list class names and each `RuleFor` chain (field, rules, messages)
- All `$.validator.addMethod()` or `$.validator.unobtrusive.adapters.add()` calls in **custom JS files only** (scan `wwwroot/js/`, `Scripts/`, and any non-library project folder — exclude `wwwroot/lib/`, `node_modules/`, and all vendor/minified files) — list method names and logic
- All `data-val-remote` attributes — list endpoint URLs and field names

---

### 2.7 — Middleware, Filters, Model Binders

Scan for:
- Classes implementing `IMiddleware`, inheriting `DelegatingHandler`, or following the `Use(...) / Run(...)` convention
- Classes implementing `IActionFilter`, `IAsyncActionFilter`, `IExceptionFilter`, `IResultFilter`
- Classes implementing `IModelBinder` or `IModelBinderProvider`
- Custom Tag Helpers (`TagHelper` subclasses) and HTML Helpers (extension methods on `IHtmlHelper`)

For each, record: class name, purpose, which controllers/actions use it.

---

### 2.8 — Authentication & Authorization

Scan `Program.cs` / `Startup.cs` for:
- Auth scheme configured (Cookie, JWT, Windows, OpenIdConnect, etc.)
- Identity configuration (`AddIdentity`, `AddDefaultIdentity`)
- Roles and custom policies defined (`AddAuthorization(options => ...)`)
- `[Authorize(Roles = "...")]` / `[Authorize(Policy = "...")]` annotations across controllers — list each unique role/policy name used

---

### 2.9 — Third-Party Libraries

Scan `package.json`, `bower.json`, `bundleconfig.json`, `_BundleConfig.cs`, and NuGet `.csproj` for:
- CDN script tags in `_Layout.cshtml` (jQuery, Bootstrap, Kendo, etc.)
- All NuGet packages relevant to migration: AutoMapper, FluentValidation, MediatR, Hangfire, Quartz, Polly, Serilog, etc.
- All client-side JS libraries used and their version

---

### 2.10 — Static Assets & CSS

Scan `wwwroot/` for:
- All CSS files — list paths and approximate size description
- All custom JS files in `wwwroot/js/` — list paths and purpose
- `bundleconfig.json` / `_BundleConfig.cs` — list each bundle, its output path, and all input files
- All image assets and font files

---

### 2.11 — SignalR Hubs

Scan for classes inheriting `Hub` or `Hub<T>`.

For each hub, record:
- Class name and namespace
- All server methods (`[HubMethodName]` or public method names)
- All `Clients.*` calls (what events are pushed to clients)
- How the hub is mapped in `Program.cs`

---

### 2.12 — Background Jobs

Scan for:
- Hangfire job registrations (`RecurringJob.AddOrUpdate`, `BackgroundJob.Enqueue`)
- Quartz.NET jobs (`IJob` implementations, scheduler configuration)
- `IHostedService` / `BackgroundService` implementations

For each, record: class name, schedule/trigger, purpose.

---

### 2.13 — File Upload Endpoints

List every action that accepts `IFormFile` or `IFormFileCollection`. Record:
- Controller + action name
- File size limits
- Allowed file types / extensions
- Where files are stored (local path, cloud, etc.)

---

### 2.14 — Localization

Scan for:
- `.resx` resource files — list file names and key count
- `IStringLocalizer<T>` / `IHtmlLocalizer<T>` / `IViewLocalizer` usage
- Localized FluentValidation messages (`WithMessage()` with string resource)
- `data-val-*` attributes with localized messages

If none found: record "No localization detected — skip i18n migration."

---

### 2.15 — MVC Areas

Scan `Areas/` folder (if present). For each area, record:
- Area name
- Controllers inside it
- Layout override (`_Layout.cshtml` inside area)

---

## Step 3: Analyze Destination Projects

### 3.1 — Destination Frontend Analysis

**[ANGULAR ONLY]** — Scan the Angular project:
- `package.json` — record Angular version, installed UI libraries (Kendo Angular, Angular Material, Bootstrap, ngx-toastr, ngx-translate, etc.), routing library, form library, HTTP client setup
- `angular.json` — note build configuration, standalone vs NgModule pattern
- `src/app/` folder structure — note existing feature folders, shared/core folder organization
- Existing interceptors (find files matching `*.interceptor.ts`) — list names and purposes
- Existing guards (find files matching `*.guard.ts`) — list names
- Existing services (find files matching `*.service.ts`) — list names
- Existing shared components — list names
- Routing setup (`app.routes.ts` or `app-routing.module.ts`) — note routing style (standalone routes or NgModule), lazy loading pattern
- `environment.ts` / environment files — note `apiUrl` or API base URL config key
- Angular version: determine control flow syntax to use (`@if`/`@for` for v17+, `*ngIf`/`*ngFor` for v16 and below)
- CSS/styling approach — note if SCSS, CSS, scoped styles are used

**[REACT ONLY]** — Scan the React project:
- `package.json` — record React version, installed UI libraries (Kendo React, MUI, Ant Design, Tailwind, react-hook-form, yup, zod, axios, react-query, zustand, redux, react-toastify, react-i18next, etc.)
- Bundler: detect `vite.config.ts`/`.js` (Vite), `react-scripts` in scripts (CRA), or custom webpack
- `src/` folder structure — note existing folder conventions: `pages/`, `components/`, `hooks/`, `services/`, `context/`, etc.
- Existing custom hooks (find files matching `use*.ts`) — list names
- Existing API service files (find `*service.ts`, `*api.ts`, `*Service.ts`) — list names
- Existing context providers or state stores — list names
- Routing setup (`App.tsx` or router config) — note routing library (react-router-dom v5/v6), route protection pattern
- Env config (`.env`, `.env.development`) — note `VITE_API_URL` or `REACT_APP_API_URL` if present
- Validation library already in use: yup or zod (check package.json)
- CSS/styling approach — CSS Modules, Tailwind, styled-components, plain CSS

---

### 3.2 — Destination Web API Analysis

Scan the Web API project:
- `.csproj` — record all NuGet packages: EF Core version, AutoMapper, FluentValidation, Serilog, MediatR, etc.
- `Program.cs` / `Startup.cs` — record middleware pipeline order, DI registrations for services, DbContext, auth, CORS, Swagger
- Existing controllers — note naming convention, base class used, response wrapper pattern (if any)
- Existing DTOs — note folder location, naming pattern (e.g., `*Dto.cs`, `*Request.cs`, `*Response.cs`)
- Existing services/interfaces — note folder location and naming pattern
- Existing DbContext — note class name, namespace, folder, EF Core config style (Fluent API vs data annotations)
- AutoMapper profiles — note folder location and mapping registration style
- Existing repository layer (if any) — note pattern used
- `appsettings.json` — note connection string key, JWT settings key, CORS origins key
- Auth scheme already configured — JWT, Identity, both?
- CORS policy — note allowed origins, check if frontend URL is already included
- `appsettings.*.json` files present — list all environment-specific config files

---

## Step 4: Resolve All Migration Decisions

Using the data gathered in Steps 2 and 3, resolve every decision that `migration.md` leaves conditional. Record the final, definitive answer for each:

### 4.1 — Library Resolution Table

For each MVC library found in the source, record the **exact package to use** in the destination (already installed → use it; not installed → use first default from migration.md):

| Source Library | Decision | Package to Use |
|---|---|---|
| Kendo UI | [installed/not installed/N/A] | [exact package or N/A] |
| Bootstrap | [installed/not installed] | [exact package] |
| jQuery Validation | [N/A — replaced by framework] | [framework form lib] |
| DataTables | [installed/not installed/N/A] | [exact package or N/A] |
| Select2 | [installed/not installed/N/A] | [exact package or N/A] |
| Toastr / SweetAlert | [installed/not installed] | [exact package] |
| Bing Maps | [found/not found] | [Bing Maps V8 SDK / N/A] |
| AutoMapper (API) | [installed/not installed] | [exact package] |
| FluentValidation (API) | [installed/not installed] | [exact package] |
| EF Core (API) | [installed/version] | [exact package version] |
| Validation schema (frontend) | [yup/zod/neither] | [exact package] |

---

### 4.2 — Naming Convention Resolution

Based on destination project scan, confirm or override default naming from `migration.md`:

**[ANGULAR ONLY]:**
- Component file pattern: `{source-view-name}.component.ts` ← confirm or record override
- Service file pattern: `{controller-name}.service.ts` ← confirm or record override
- Model/interface pattern: `{dto-name}.model.ts` ← confirm or record override
- Feature folder location: `src/app/{feature-name}/` ← confirm or record actual path
- Routing style: standalone routes or NgModule ← record which

**[REACT ONLY]:**
- Page component pattern: `{SourceViewName}Page.tsx` ← confirm or record override
- Service/hook file pattern: `{feature}Service.ts` or `{feature}Api.ts` ← confirm which
- Interface/type file pattern: `{dto-name}.types.ts` ← confirm or record override
- Pages folder location: `src/pages/{feature-name}/` ← confirm or record actual path
- Routing pattern: react-router-dom version and route definition style ← record

**Web API (both):**
- Controller convention: note if destination uses `[ApiController]` with `ControllerBase` ← confirm
- DTO folder: record actual path
- Service + interface folder: record actual path
- AutoMapper profile folder: record actual path
- DI registration location: `Program.cs` inline, extension method, or module ← record

---

### 4.3 — Angular Version Syntax (Angular only)

Determine Angular version from `package.json`:
- If v17+: all generated templates use `@if` / `@for` / `@empty` control flow
- If v16 or below: all generated templates use `*ngIf` / `*ngFor` / `*ngSwitch`
Record this decision explicitly so `migration-phase.md` enforces it uniformly.

---

### 4.4 — CORS Verification

Check the Web API's CORS policy:
- Is the destination frontend origin already in the allowed origins list?
- If not, flag: "**⚠ CORS ACTION REQUIRED before Phase 2**" and record the frontend URL to add.

---

### 4.5 — Controller Processing Order

Produce the final ordered list of controllers for migration:
1. Auth/Account controllers (sorted alphabetically if multiple)
2. All remaining controllers in alphabetical order
3. Complex controllers last (SignalR-heavy, file-upload-heavy — flag these)

For each controller in the list, record:
- Estimated complexity: LOW / MEDIUM / HIGH (based on action count, validation count, special features)
- Special features: SignalR, file upload, Bing Maps, Kendo, Areas, background jobs (list which apply)

---

## Step 5: Produce the Inventory Summary

Print a structured inventory summary to the user covering all findings from Step 2 and 3. Format:

```
=== SOURCE PROJECT INVENTORY ===

Controllers: [N total]
  [list each controller with action count]

Views: [N total]
  [list grouped by controller]

ViewModels: [N total]
  [list class names]

EF Core Entities: [N total]
  [list entity class names and DbContext]

Third-Party Libraries:
  [list each detected library]

Client-Side Validations:
  [list each form with its data-val-* rules]

Server-Side Validations:
  [list each ViewModel/DTO with its rules]

FluentValidation Validators:
  [list each validator class with field rules]

AutoMapper Profiles:
  [list each mapping]

SignalR Hubs: [N / none]
  [list hub names]

Background Jobs: [N / none]
  [list job names]

Custom Middleware / Filters:
  [list each]

MVC Areas: [N / none]
  [list area names]

File Upload Endpoints:
  [list controller + action]

Localization: [yes / no]

Bing Maps Usage: [yes / no — list views if yes]

Custom Error Pages:
  [list found: 404, 500, 403, etc.]

=== DESTINATION FRONTEND INVENTORY ===
Framework: [Angular vX / React vX]
Bundler: [Vite / CRA / webpack — React only]
UI Libraries installed: [list]
Routing setup: [describe]
Existing interceptors/guards/hooks: [list]
API base URL config: [var name and current value]
CSS approach: [SCSS / CSS Modules / Tailwind / plain CSS]
Angular control flow syntax: [@if/@for / *ngIf/*ngFor — Angular only]

=== DESTINATION WEB API INVENTORY ===
EF Core: [version]
AutoMapper: [installed / not installed]
FluentValidation: [installed / not installed]
Auth: [JWT / Identity / both / none — current state]
CORS: [configured / missing — flag if frontend origin not present]
Existing DI registrations: [summary]
```

**Present the inventory summary to the user and wait for confirmation before proceeding to Step 6.**

Ask:
> "Does this inventory look correct? Please confirm or point out any discrepancies before I generate migration-phase.md. (confirm / [corrections])"

Incorporate any corrections from the user, then proceed.

---

## Step 5.5: Save Analysis Checkpoint

After the user confirms the inventory, **before generating `migration-phase.md`**, write a file `ANALYSIS_PROGRESS.md` to the workspace root with the following content:

    # Analysis Progress Checkpoint
    <!-- Written after user confirmed inventory. Resume Step 6 from here if output is truncated. -->

    ## Status
    - [x] Step 1: Configuration collected
    - [x] Step 2: Source project scanned
    - [x] Step 3: Destination projects scanned
    - [x] Step 4: Decisions resolved
    - [x] Step 5: Inventory confirmed by user
    - [ ] Step 6: migration-phase.md generated

    ## Resolved Configuration
    [Paste the filled-in Resolved Configuration table from Step 4]

    ## Controller Order
    [Paste the ordered controller list from Step 4.5]

    ## Library Resolution
    [Paste the filled-in Library Resolution Table from Step 4.1]

**Resume rule:** If `migration-phase.md` generation is interrupted (session timeout, truncated output), on the next session:
1. Read `ANALYSIS_PROGRESS.md` to restore all resolved configuration and controller order
2. Regenerate only `migration-phase.md` from the checkpoint — do NOT re-scan the source or destination projects
3. Once `migration-phase.md` is confirmed complete and correct, delete `ANALYSIS_PROGRESS.md`

---

## Step 6: Generate `migration-phase.md`

After inventory is confirmed, generate the file `migration-phase.md` in the workspace root. This file **is the executable migration plan** — it is fully concrete, with all conditional branches already resolved, all library choices already made, and all controllers listed in exact execution order.

**The file must follow this exact structure:**

---

# Migration Execution Plan
<!-- Generated by analysis.md on [date]. Do NOT edit manually — re-run analysis.md to regenerate. -->
<!-- Source: [source project path] -->
<!-- Frontend: [destination frontend path] — [Angular vX / React vX] -->
<!-- Web API: [destination Web API path] -->
<!-- Kendo: [yes — vX / no] -->

## Session Resilience

This plan may span multiple sessions. A `MIGRATION_PROGRESS.md` tracker will be created in the
destination frontend project root after Phase 1 is confirmed. On resume, read that file to
determine current position — do NOT restart from scratch.

---

## Resolved Configuration

| Setting | Value |
|---|---|
| Frontend Framework | [Angular vX / React vX] |
| Angular control flow | [@if/@for / *ngIf/*ngFor — Angular only] |
| Bundler | [Vite / CRA — React only] |
| Validation library | [Reactive Forms / react-hook-form + yup / react-hook-form + zod] |
| Notification library | [ngx-toastr / react-toastify / sweetalert2] |
| HTTP client | [HttpClient / axios / fetch] |
| Kendo version | [vX.Y / N/A] |
| CORS status | [OK / ⚠ Action required — add [origin] to Web API CORS policy] |
| Component file pattern | [exact pattern] |
| Service file pattern | [exact pattern] |
| DTO folder | [exact path] |
| Service folder | [exact path] |
| AutoMapper profile folder | [exact path] |
| Angular syntax | [@if/@for / *ngIf/*ngFor] |

---

## Library Resolution

[Insert the filled-in Library Resolution Table from Step 4.1]

---

## Workspace Modification Permission

Before starting migration work, ask the user:

**"This migration will create, modify, and reorganize files across your frontend and Web API projects. Do you grant permission to modify your workspace for the entire migration operation? (yes/no)"**

- Yes → proceed without per-file confirmation.
- No → ask before each file operation.

---

## One-Time Setup Checklist

Complete these once before starting any controller migration:

**Web API:**
- [ ] Verify JWT Bearer auth is configured in `Program.cs`
- [ ] Verify CORS policy includes frontend origin [list resolved origin]
- [ ] [FLAG if CORS action required: add specific origin to CORS policy]
- [ ] Verify `appsettings.json` has connection string key `[resolved key name]`
- [ ] Add `appsettings.Staging.json` and `appsettings.Production.json` if missing
- [ ] [If Bing Maps]: Add `"BingMaps": { "ApiKey": "" }` to `appsettings.json`

**[ANGULAR ONLY] Frontend:**
- [ ] Set `apiUrl` in `environment.ts` / `environment.development.ts` / `environment.prod.ts`
- [ ] [If Bing Maps]: Install `bingmaps` types, add `/// <reference types="bingmaps" />`, load script in `index.html`, add `bingMapsKey: ''` to environment files
- [ ] [If localization]: Set up `@ngx-translate/core` with translation JSON files [list locales found]
- [ ] [If SignalR]: Confirm `@microsoft/signalr` is installed

**[REACT ONLY] Frontend:**
- [ ] Set `VITE_API_URL` / `REACT_APP_API_URL` in `.env.local`, `.env.development`, `.env.production`
- [ ] [If Bing Maps]: Install `bingmaps` types, set up loader hook, add `VITE_BINGMAPS_KEY=` to `.env`
- [ ] [If localization]: Set up `react-i18next` with translation JSON files [list locales found]
- [ ] [If SignalR]: Confirm `@microsoft/signalr` is installed

---

## Phase 1: Auth Setup (Migrate First)

[Only if auth/account controllers exist in source]

### Auth UI Migration
- [ ] Create login page component with form validation
  - Fields: [list fields from source login ViewModel with their validation rules]
  - On success: store JWT in [localStorage/sessionStorage] and redirect to [resolved route]
- [ ] Create register page component with form validation
  - Fields: [list fields from source register ViewModel with their validation rules]
- [ ] [If other account management pages exist, list them]

**[ANGULAR ONLY]:**
- [ ] Create `auth.interceptor.ts` at `[resolved path]` — attaches `Authorization: Bearer` header
- [ ] Create `auth.guard.ts` at `[resolved path]` — `CanActivateFn` checking for valid JWT
- [ ] Add auth routes to `[resolved routing file]`

**[REACT ONLY]:**
- [ ] Create axios interceptor (or extend `[existing interceptor file if found]`) — attaches `Authorization: Bearer` header
- [ ] Create `ProtectedRoute` component at `[resolved path]` — checks for JWT, redirects to login if missing
- [ ] Add auth routes to `[resolved router file]`

---

## Phase 2: Backend Migration

> Process controllers in this order: [list resolved controller order from Step 4.5]

### DbContext & EF Core Migration (One-Time)
- [ ] Destination DbContext: `[class name]` at `[path]`
- [ ] Add missing `DbSet<T>` properties: [list each entity from source not yet in destination]
- [ ] Migrate entity configurations: [list each `IEntityTypeConfiguration<T>` class to migrate]
- [ ] Migrate global query filters: [list each `HasQueryFilter(...)` found]
- [ ] Migrate seed data: [list each `HasData(...)` block]
- [ ] Migrate EF interceptors: [list each interceptor class]
- [ ] Run `dotnet ef migrations add InitialMigration` after all entities are added
- [ ] Update `appsettings.json` with connection string key `[resolved key]`

---

[For each controller in the resolved order, generate a section:]

### Controller: [ControllerName] — [LOW/MEDIUM/HIGH complexity]
[Special features: list applicable — SignalR, file upload, Bing Maps, Kendo, Area name]

**Backend:**
- [ ] Create `[ControllerName]Controller.cs` at `[resolved path]`
  - Actions to migrate: [list each action with HTTP verb and route]
  - `[Authorize]` attributes: [list roles/policies, or "none"]
- [ ] Create interface `I[ServiceName].cs` at `[resolved service folder]`
- [ ] Create implementation `[ServiceName].cs` at `[resolved service folder]`
  - Methods: [list each method name]
- [ ] Create DTOs at `[resolved DTO folder]`:
  - [list each DTO class name, derived from ViewModel name → Dto suffix]
  - Validation rules per DTO: [list each property and its data annotations]
  - FluentValidation rules: [list each RuleFor chain if FluentValidation used]
- [ ] Create AutoMapper profile `[FeatureName]MappingProfile.cs` at `[resolved profile folder]`
  - Mappings: [list each `CreateMap<Entity, Dto>()` pair]
- [ ] Register `I[ServiceName]` → `[ServiceName]` in DI at `[Program.cs or extension method path]`
- [ ] [If file upload]: Migrate endpoint to accept `[FromForm]` multipart — size limit: [value], allowed types: [list]
- [ ] [If custom filter on this controller]: Migrate `[FilterClass]` to Web API `[ActionFilter/middleware]`

**Frontend [ANGULAR ONLY]:**
- [ ] Create `[feature-name]/` folder at `[resolved src/app/feature-name/ path]`
- [ ] Create TypeScript model `[dto-name].model.ts` — properties: [list each]
- [ ] Create `[controller-name].service.ts` — methods: [list each, matching API actions]
- [ ] Create list component `[source-view-name].component.ts` + template
  - Data: calls `[service].getAll()` / `[service].getList()`
  - [If Kendo Grid]: use `<kendo-grid>` with columns: [list column bindings]
- [ ] Create detail component `[source-view-name].component.ts` + template (if Details view exists)
- [ ] Create create/edit form component `[source-view-name].component.ts` + template
  - Form fields and validators:
    [For each field, list: fieldName | controlName | Validators to apply | error messages]
  - [If cross-field validation]: create custom `ValidatorFn` for [describe rule]
  - [If remote/async validation]: create `AsyncValidatorFn` calling `[API endpoint]`
  - [If validation summary]: create form-level error summary component
- [ ] Add routes to `[resolved routing file]`:
  - `[route path]` → list component
  - `[route path]/:id` → detail/edit component
- [ ] [If Bing Maps view]: Create `BingMapComponent` at `[path]` using Direct Bing Maps V8 SDK
- [ ] [If SignalR]: Wire `[SignalR service]` into component — subscribe to `[events list]`
- [ ] Migrate CSS from `[source CSS file(s)]` to `[resolved destination path]`

**Frontend [REACT ONLY]:**
- [ ] Create `[feature-name]/` folder at `[resolved src/pages/feature-name/ path]`
- [ ] Create TypeScript interface `[dto-name].types.ts` — properties: [list each]
- [ ] Create `[feature]Service.ts` / `[feature]Api.ts` (per resolved pattern) — methods: [list each]
- [ ] Create `[SourceViewName]Page.tsx` for list view
  - Data fetching: `[hook/service method]`
  - [If Kendo Grid]: use `<Grid>` with columns: [list column bindings]
- [ ] Create `[SourceViewName]Page.tsx` for detail view (if Details view exists)
- [ ] Create `[SourceViewName]Page.tsx` for create/edit form
  - Yup schema (or zod per resolved decision):
    [For each field, list: fieldName | yup rule chain | error message]
  - [If cross-field]: add `.oneOf()` or `.test()` with condition: [describe]
  - [If remote async]: add `.test()` calling `[API endpoint]`
  - [If validation summary]: add form-level error summary component
- [ ] Add routes to `[resolved router file]`:
  - `[route path]` → list page
  - `[route path]/:id` → detail/edit page
- [ ] [If Bing Maps view]: Create `BingMap.tsx` at `[path]` using Direct Bing Maps V8 SDK
- [ ] [If SignalR]: Wire SignalR hook into component — subscribe to `[events list]`
- [ ] Migrate CSS from `[source CSS file(s)]` to `[resolved destination path]`

---

[Repeat the controller section for every controller in the resolved order]

---

## Phase 3: Static Assets & CSS Migration

- [ ] Copy `wwwroot/images/` → `[resolved destination assets path]`
- [ ] Copy `wwwroot/fonts/` → `[resolved destination assets path]` (if present)
- [ ] Migrate CSS files:
  [For each CSS file found in source, list: source path → resolved destination path]
- [ ] Migrate custom JS bundles (after removing jQuery and jQuery plugins):
  [For each custom JS file in bundles, list: source path → resolved destination component/hook/service]
- [ ] Migrate shared partial styles from `Views/Shared/` inline `<style>` blocks → `[resolved global stylesheet]`
- [ ] Migrate error page CSS → error page components' styles

---

## Phase 4: Custom Error Pages

- [ ] [For each error page found — 404, 500, 403, etc.]:
  - Create `[ErrorPageName]Page.tsx` / `[error-page-name].component.ts` at `[resolved path]`
  - Apply CSS from source `[error page CSS]`
  - Wire into router wildcard / HTTP interceptor

---

## Phase 5: Verification Checklist

> Run this after all controllers are migrated.

**Build verification:**
- [ ] Web API builds with 0 errors (`dotnet build`)
- [ ] Frontend builds with 0 errors ([Angular: `ng build`] / [React: `npm run build` or `vite build`])

**Runtime verification — for each migrated controller:**
- [ ] [ControllerName]: API endpoints return expected responses (test in Swagger / Postman)
- [ ] [ControllerName]: List page loads and displays data
- [ ] [ControllerName]: Create form validates correctly (client-side) and submits
- [ ] [ControllerName]: Edit form loads existing data and validates on submit
- [ ] [ControllerName]: Delete action works
- [ ] [ControllerName]: All `[Authorize]` restrictions enforce correctly

**Cross-cutting verification:**
- [ ] Auth flow: login → JWT stored → protected routes accessible → logout clears token
- [ ] Server-side validation errors (400 ProblemDetails) displayed inline in forms
- [ ] [If Bing Maps]: Maps load, pushpins/infoboxes/polylines render correctly
- [ ] [If SignalR]: Real-time events fire and update UI
- [ ] [If file upload]: Files upload successfully with correct size/type validation
- [ ] [If localization]: All UI strings appear in correct locale
- [ ] [If background jobs]: Jobs execute on schedule
- [ ] CSS visually matches source application on all pages
- [ ] Responsive breakpoints match source application

---

## Step 7: Confirm File Written

After writing `migration-phase.md`, print:

```
✅ Analysis complete. migration-phase.md has been written to [workspace root].

Summary:
- Controllers to migrate: [N]
- Estimated complexity: [N LOW / N MEDIUM / N HIGH]
- Special features detected: [list: SignalR, Bing Maps, Kendo, file upload, localization, MVC Areas, background jobs — or "none"]
- CORS status: [OK / ⚠ Action required]
- One-time setup items: [N]
- Resolved framework: [Angular vX / React vX]
- Resolved validation library: [name]

Next step: Open migration-phase.md and execute it to perform the migration.
```
