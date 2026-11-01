from flask import Blueprint, request, jsonify
from repository.permissionRepository import PermissionRepository
from db_connection import SessionLocal
from dto.permissionDTO import PermissionDTO

permission_bp = Blueprint('permission_bp', __name__, url_prefix='/permissions')

# ===================== יצירת הרשאה =====================
@permission_bp.route('', methods=['POST'])
def add_permission():
    db_session = SessionLocal()
    try:
        repo = PermissionRepository(db_session)
        data = request.get_json()
        new_permission = repo.create_permission(type=data['type'])

        dto = PermissionDTO(id=new_permission.id, type=new_permission.type)
        return jsonify(dto.__dict__), 201
    finally:
        db_session.close()


# ===================== קבלת הרשאה לפי ID =====================
@permission_bp.route('/<int:permission_id>', methods=['GET'])
def get_permission(permission_id):
    db_session = SessionLocal()
    try:
        repo = PermissionRepository(db_session)
        permission = repo.get_permission(permission_id)
        if not permission:
            return jsonify({'error': 'Permission not found'}), 404

        dto = PermissionDTO(id=permission.id, type=permission.type)
        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ===================== קבלת כל ההרשאות =====================
@permission_bp.route('', methods=['GET'])
def get_all_permissions():
    db_session = SessionLocal()
    try:
        repo = PermissionRepository(db_session)
        permissions = repo.get_all_permissions()
        dto_list = [PermissionDTO(id=p.id, type=p.type).__dict__ for p in permissions]
        return jsonify(dto_list)
    finally:
        db_session.close()


# ===================== עדכון הרשאה =====================
@permission_bp.route('/<int:permission_id>', methods=['PUT'])
def update_permission(permission_id):
    db_session = SessionLocal()
    try:
        repo = PermissionRepository(db_session)
        data = request.get_json()
        updated_permission = repo.update_permission(permissionID=permission_id, type=data.get('type'))

        if not updated_permission:
            return jsonify({'error': 'Permission not found'}), 404

        dto = PermissionDTO(id=updated_permission.id, type=updated_permission.type)
        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ===================== מחיקת הרשאה =====================
@permission_bp.route('/<int:permission_id>', methods=['DELETE'])
def delete_permission(permission_id):
    db_session = SessionLocal()
    try:
        repo = PermissionRepository(db_session)
        success = repo.delete_permission(permission_id)
        if not success:
            return jsonify({'error': 'Permission not found'}), 404
        return jsonify({'message': 'Permission deleted successfully'})
    finally:
        db_session.close()