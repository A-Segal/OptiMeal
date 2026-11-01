from sqlalchemy.orm import Session
from models.permission import Permission

class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_permission(self, type: str) -> Permission:
        permission = Permission(type=type)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def get_permission(self, permissionID: int) -> Permission | None:
        return self.db.query(Permission).filter(Permission.id == permissionID).first()

    def get_all_permissions(self) -> list[Permission]:
        return self.db.query(Permission).all()

    def update_permission(self, permissionID: int, type: str) -> Permission | None:
        permission = self.get_permission(permissionID)
        if permission:
            permission.type = type
            self.db.commit()
            self.db.refresh(permission)
        return permission

    def delete_permission(self, permissionID: int) -> bool:
        permission = self.get_permission(permissionID)
        if permission:
            self.db.delete(permission)
            self.db.commit()
            return True
        return False