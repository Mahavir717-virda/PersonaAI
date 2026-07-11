# Gmail Flow Only

## 1. Background Sync Flow

```mermaid
flowchart TD
    A[User opens Gmail UI] --> B[Frontend requests /api/v1/connectors/gmail/messages]
    B --> C{refresh=true?}
    C -- yes --> D[SyncService.trigger_sync]
    C -- no --> J[Read stored messages]
    D --> E[Load connector and credentials]
    E --> F[connector.sync(cursor)]
    F --> G[GmailProvider.fetch_messages_since_history or fetch_messages_page]
    G --> H[Fetch Gmail change set or message list]
    H --> I[Fetch each message detail]
    I --> K[CommunicationPipeline.process_payload]
    K --> L[Normalize]
    L --> M[Deduplicate]
    M --> N[Create conversation]
    N --> O[Persist communication]
    O --> P[Persist attachments]
    P --> Q[Update checkpoint]
    Q --> R[Update sync history]
    R --> S[Return stored Gmail messages]
    J --> S
```

```mermaid
sequenceDiagram
    autonumber
    participant UI as Frontend
    participant API as Connectors API
    participant Sync as SyncService
    participant Conn as GmailConnector
    participant Prov as GmailProvider
    participant Pipe as CommunicationPipeline
    participant DB as Database

    UI->>API: GET /api/v1/connectors/gmail/messages?refresh=true
    API->>Sync: trigger_sync(user_id, "gmail")
    Sync->>Conn: get_connector(...)
    Sync->>Conn: sync(cursor)
    Conn->>Prov: fetch_messages_page(...)
    Prov-->>Conn: raw Gmail records
    Conn->>Pipe: process_payload("gmail", raw_record)
    Pipe->>DB: normalize + dedupe + save
    Pipe->>DB: create conversation + attachments
    Pipe-->>Sync: Communication or None
    Sync->>DB: update checkpoint
    Sync->>DB: update sync history + connector state
    API->>DB: read stored communications
    API-->>UI: GmailMessagesResponse
```

### Current State

- Manual sync exists.
- Incremental cursor checkpoint exists.
- Sync history exists.
- Background sync scheduling is wired through the extension alarm loop.
- Gmail History API incremental sync is implemented in the provider.

## 2. Unified Inbox Flow

```mermaid
flowchart TD
    A[Gmail provider payload] --> B[GmailConnector.normalize]
    B --> C[Communication model]
    C --> D[CommunicationPipeline]
    D --> E[Database communications table]
    E --> F[Unified inbox API]
    F --> G[Frontend Gmail inbox]
```

```mermaid
sequenceDiagram
    autonumber
    participant Gmail as GmailProvider
    participant Conn as GmailConnector
    participant Pipe as CommunicationPipeline
    participant Repo as CommunicationRepository
    participant UI as GmailPage

    Gmail->>Conn: raw message record
    Conn->>Pipe: normalized communication
    Pipe->>Repo: create_communication
    Repo-->>Pipe: persisted record
    UI->>Repo: GET /api/v1/communications?platform=gmail
    Repo-->>UI: normalized inbox records
```

### Current State

- Unified inbox reads from `communications`.
- Gmail inbox still has a connector-specific read path for loading and refresh.
- The shared communications table already supports a unified inbox pattern.

## 3. Email Actions Flow

```mermaid
flowchart TD
    A[User clicks Reply / Archive / Delete / Star] --> B[Extension or UI action]
    B --> C{Backend endpoint exists?}
    C -- no --> D[Action not implemented]
    C -- yes --> E[Update Gmail]
    E --> F[Update local communication state]
    F --> G[Refresh inbox]
```

### Current State

- Reply is not implemented.
- Reply All is not implemented.
- Forward is not implemented.
- Archive is not implemented.
- Delete is not implemented.
- Mark Read and Mark Unread are not implemented.
- Star and Unstar are not implemented.
- Label move/update is not implemented.

## 4. Exact Backend Reality

```mermaid
flowchart TD
    A[Google login] --> B[JWT issued]
    B --> C[Connector connect]
    C --> D[Manual Gmail sync]
    D --> E[Normalize and persist]
    E --> F[Unified communications read]
    F --> G[Extension or frontend renders inbox]
```

```mermaid
flowchart TD
    H[Background scheduler] --> I[Not wired]
    J[Gmail History API] --> K[Not wired]
    L[Message action endpoints] --> M[Not wired]
```
