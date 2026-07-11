    # Backend Architecture Refactor Proposal

    ## Purpose

    This proposal re-organizes the backend into a Domain-Driven Vertical Slice architecture without changing public behavior, endpoints, OAuth logic, database models, migrations, API contracts, or frontend integration.

    This is an architecture refactoring task only. No new connectors, no new features, and no AI logic implementation are included.

    ## Non-goals

    - Do not add new communication platforms.
    - Do not add new connectors.
    - Do not change user-visible behavior.
    - Do not introduce new business capabilities beyond the current Gmail and brain boundaries.
    - Do not move files yet. This document is the implementation contract for review.

    ---

    ## Target Architecture Principles

    1. Organize by business capability rather than technical layer.
    2. Make Gmail a self-contained feature slice.
    3. Make the AI Brain its own subsystem with explicit internal boundaries.
    4. Move infrastructure concerns into platform/shared modules.
    5. Preserve dependency direction:
    - Feature -> Service -> Repository -> Database
    - Never the reverse
    6. Keep public API routes backward compatible.
    7. Remove duplicate ownership and eliminate circular dependencies.

    ---

    ## Proposed Backend Structure

    ```text
    backend/app/
    api/
        v1/
        routes/
            auth.py
            communications.py
            connectors.py
            health.py

    auth/
        api/
        application/
        domain/
        infrastructure/

    communication/
        gmail/
        api/
        application/
        domain/
        infrastructure/
        shared/

    connectors/
        registry/
        manifests/
        interfaces/

    brain/
        orchestrator/
        memory/
        knowledge/
        rag/
        response/
        planning/
        tasks/
        learning/
        shared/

    platform/
        database/
        config/
        logging/
        middleware/
        security/
        storage/
        scheduler/
        workers/
        notifications/

    shared/
        exceptions/
        enums/
        constants/
        utils/
        schemas/
    ```

    ---

    ## Module Responsibilities

    ### 1. Auth slice

    Purpose: user identity, JWT handling, session lifecycle, and auth-related workflows.

    Responsibilities:
    - Authentication API endpoints
    - Token and session orchestration
    - User identity and authorization boundaries
    - Auth-related services and repositories

    Dependencies:
    - May depend on platform and shared modules
    - Must not depend on communication or brain internals

    ### 2. Communication slice

    Purpose: model communication workflows as a business domain, currently centered on Gmail.

    Responsibilities:
    - Inbox/message ingestion workflows
    - OAuth flow for Gmail
    - Gmail provider integration
    - Sync orchestration
    - Messaging normalization and persistence
    - Communication domain models and mapping logic

    Dependencies:
    - Depends on platform database/config/security/storage modules
    - Depends on shared schemas and exceptions
    - Must remain isolated from brain internals

    ### 3. Gmail feature slice

    Purpose: make Gmail completely self-contained.

    Responsibilities:
    - Gmail routes and API handlers
    - Gmail OAuth implementation
    - Gmail provider client
    - Gmail sync service
    - Gmail repository and persistence mapping
    - Gmail schemas and response serialization
    - Gmail-specific domain logic

    This slice should own all Gmail-specific code, including:
    - API
    - OAuth
    - Provider
    - Sync
    - Repository
    - Schemas
    - Models
    - Services
    - Mapping

    No other feature slice should own Gmail-specific logic.

    ### 4. Brain subsystem

    Purpose: create an explicit boundary for future AI orchestration work.

    Responsibilities:
    - LangGraph orchestrator boundary
    - Memory engine boundary
    - Knowledge engine boundary
    - RAG engine boundary
    - Response engine boundary
    - Planning engine boundary
    - Task engine boundary
    - Learning engine boundary

    The brain subsystem should expose only a narrow application-facing interface to the rest of the backend.

    It should not directly depend on Gmail-specific implementation details. Instead, it should consume normalized communication abstractions.

    ### 5. Platform module

    Purpose: host all infrastructure concerns.

    Responsibilities:
    - Database access and session management
    - Configuration and environment settings
    - Logging and observability
    - Middleware and request lifecycle concerns
    - Security primitives
    - Storage abstractions
    - Scheduler and worker execution
    - Notifications and background processing

    The platform layer should be reusable and dependency-inverted.

    ### 6. Shared module

    Purpose: host common primitives that are not feature-owned.

    Responsibilities:
    - Common exceptions
    - Enums
    - Constants
    - Utility functions
    - Cross-cutting schemas
    - Reusable types

    ---

    ## Dependency Rules

    The architecture will enforce the following direction:

    - API layer may call application services
    - Application services may call domain services and repositories
    - Repositories may call database abstractions
    - Platform modules may be consumed by feature modules
    - Shared modules may be consumed by both feature and platform modules

    Forbidden patterns:
    - Feature modules importing from API layer
    - Repositories importing from services
    - Brain modules importing Gmail-specific route or provider code
    - Platform modules depending on feature logic

    In short:

    ```text
    API -> Application -> Domain -> Infrastructure -> Platform
    ```

    and:

    ```text
    Feature Slice -> Shared/Platform
    ```

    Never:

    ```text
    Platform -> Feature
    Feature -> API
    ```

    ---

    ## Gmail Slice Structure

    The Gmail feature should be organized as a self-contained slice:

    ```text
    communication/gmail/
    api/
        routes.py
        serializers.py
    application/
        services/
        use_cases/
    domain/
        models/
        value_objects/
        events/
    infrastructure/
        oauth/
        provider/
        sync/
        repository/
        mapping/
    ```

    This ensures Gmail-related implementation is colocated and discoverable.

    ---

    ## Brain Subsystem Structure

    The brain subsystem should be isolated and future-proof:

    ```text
    brain/
    orchestrator/
    memory/
    knowledge/
    rag/
    response/
    planning/
    tasks/
    learning/
    shared/
    ```

    Each submodule should expose a narrow interface and depend only on:
    - normalized domain models
    - shared abstractions
    - platform services

    No brain module should depend on Gmail-specific route handlers or provider classes directly.

    ---

    ## Import Refactoring Plan

    ### Phase 1: establish boundaries

    - Create the new package structure without moving behavior.
    - Introduce thin compatibility shims where needed to keep imports working during migration.
    - Keep the existing route paths unchanged.

    ### Phase 2: move feature ownership

    - Move Gmail-related code into the communication/gmail slice.
    - Move current connector route logic behind service adapters that preserve existing endpoint contracts.
    - Retain the same response schema shapes and path names.

    ### Phase 3: isolate platform concerns

    - Move database/session/config/logging/security/storage/scheduler/worker concerns under platform.
    - Update feature modules to depend on platform abstractions rather than direct infrastructure access.

    ### Phase 4: isolate brain subsystem

    - Introduce the brain boundary packages.
    - Define a narrow interface for communication ingestion into the brain subsystem.
    - Keep all AI-related internals inside the brain package.

    ### Phase 5: remove legacy coupling

    - Remove cross-module imports that bypass the new architecture.
    - Replace direct imports of technical-layer modules from feature modules.
    - Ensure circular import chains are resolved.

    ---

    ## Migration Plan

    ### Step 1: freeze current contracts

    - Document existing routes, schemas, response payloads, and OAuth behavior.
    - Preserve all endpoint paths and request/response shapes.
    - Freeze database model expectations and migration ordering.

    ### Step 2: create the target package skeleton

    - Create the proposed folders and package boundaries.
    - Add placeholder modules and import adapters.
    - Keep behavior unchanged while the structure is introduced.

    ### Step 3: migrate Gmail into its own slice

    - Move Gmail-specific routes, services, repositories, providers, schemas, and mapping logic into communication/gmail.
    - Preserve existing connectors API behavior through adapter layers.

    ### Step 4: extract infrastructure into platform

    - Relocate database, config, logging, middleware, storage, scheduler, and worker modules behind platform boundaries.
    - Ensure feature modules depend on abstractions rather than concrete infrastructure implementations.

    ### Step 5: establish the brain boundary

    - Create the brain subsystem modules.
    - Define the dependency contract between communication and brain.
    - Keep AI behavior unimplemented and only establish boundaries.

    ### Step 6: validate import graph and compatibility

    - Ensure no feature imports reverse into API or business layers.
    - Verify all existing routes still resolve and return the same payloads.
    - Run regression checks for auth, connector, and communication flows.

    ---

    ## Dependency Graph

    ```text
    API Routes
    -> Auth / Communication / Connector application services
        -> Domain services
        -> Repositories
            -> Platform database abstractions

    Communication Gmail slice
    -> Platform config/security/storage/logging
    -> Shared schemas/exceptions

    Brain subsystem
    -> Shared abstractions
    -> Communication domain interfaces
    -> Platform services

    Not allowed:
    Communication -> API
    Brain -> Gmail provider implementation directly
    Platform -> Feature logic
    ```

    ---

    ## Risk Analysis

    ### High risk: hidden coupling to legacy modules

    The current codebase likely has imports that cross technical packages in non-obvious ways. This can cause circular dependencies during migration.

    Mitigation:
    - Move one slice at a time
    - Introduce compatibility adapters
    - Refactor imports incrementally

    ### Medium risk: route contract drift

    If routing files are reorganized carelessly, endpoint payloads or statuses may change.

    Mitigation:
    - Preserve route paths and response models exactly
    - Keep route modules thin wrappers over application services

    ### Medium risk: database model ownership confusion

    If models remain distributed across packages, refactoring can create inconsistent persistence boundaries.

    Mitigation:
    - Define one persistence owner per domain object
    - Keep models close to the domain slice that owns them

    ### Medium risk: brain boundary leakage

    If the brain subsystem becomes coupled to Gmail-specific implementation details, the architecture will regress.

    Mitigation:
    - Define a communication abstraction consumed by brain modules
    - Keep Gmail-specific implementation inside the Gmail slice

    ---

    ## Execution Plan

    1. Review and approve this proposal.
    2. Create the new package skeleton without moving behavior.
    3. Introduce thin adapters that preserve existing imports.
    4. Migrate Gmail functionality into communication/gmail.
    5. Relocate infrastructure concerns into platform.
    6. Isolate the brain subsystem with explicit boundaries.
    7. Refactor imports to follow the dependency rules.
    8. Validate endpoint compatibility and remove legacy coupling.
    9. Only then begin any implementation work for the brain internals.

    ---

    ## Recommended Implementation Order

    1. Auth slice
    2. Communication/Gmail slice
    3. Platform abstraction layer
    4. Brain subsystem skeleton
    5. Import cleanup and dependency enforcement

    This order minimizes risk and preserves existing behavior while establishing the new architecture.

    ---

    ## Implementation Status

    The initial architecture skeleton has been added under the backend package without moving existing runtime behavior:

    - Added new feature-oriented packages for auth, communication, brain, platform, and shared boundaries.
    - Added placeholder modules for Gmail feature-slice application and infrastructure layers.
    - Added a platform database abstraction placeholder.
    - Added a brain subsystem boundary with interfaces for future orchestration ingestion.
    - Added shared exception primitives for dependency-boundary enforcement.

    This establishes the architectural structure for the next migration phase while keeping the current application behavior intact.
