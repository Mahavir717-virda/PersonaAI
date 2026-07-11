import os
import shutil

moves = [
    (
        "backend/app/connectors/gmail.py",
        "backend/app/communication/gmail/infrastructure/sync/gmail_connector.py",
    ),
    (
        "backend/app/providers/gmail/provider.py",
        "backend/app/communication/gmail/infrastructure/provider/gmail_provider.py",
    ),
    (
        "backend/app/repositories/connector.py",
        "backend/app/communication/gmail/infrastructure/repository/connector_repository.py",
    ),
]

for src, dst in moves:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    if os.path.exists(src):
        shutil.move(src, dst)

wrappers = {
    "backend/app/connectors/gmail.py": 'from app.communication.gmail.infrastructure.sync.gmail_connector import GmailConnector\n\n__all__ = ["GmailConnector"]\n',
    "backend/app/providers/gmail/provider.py": 'from app.communication.gmail.infrastructure.provider.gmail_provider import GmailProvider\n\n__all__ = ["GmailProvider"]\n',
    "backend/app/repositories/connector.py": 'from app.communication.gmail.infrastructure.repository.connector_repository import ConnectorRepository\n\n__all__ = ["ConnectorRepository"]\n',
}

for path, content in wrappers.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print(
    "Moved Gmail implementation files into the new slice and created compatibility wrappers"
)
