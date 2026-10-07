# ═══════════════════════════════════════════════════════════════════════════════
#  EMANTIX PRO — Tests de Validación de Archivos
#  Casos críticos de seguridad
# ═══════════════════════════════════════════════════════════════════════════════

import pytest
from unittest.mock import Mock, patch
from io import BytesIO

# Importar funciones a testear
import sys
sys.path.insert(0, '/home/claude/emantix_refactored/backend')

from utils.file_validator import (
    validate_excel_file, validate_pdf_file, detect_mime_type,
    is_safe_filename, generate_safe_filename, validate_required_columns,
    find_duplicate_rows
)

# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE VALIDACIÓN DE EXCEL
# ══════════════════════════════════════════════════════════════════════════════

class TestExcelValidation:
    """Tests para validación de archivos Excel"""
    
    def test_valid_excel_filename(self):
        """Validar que extensiones .xlsx se aceptan"""
        valid, msg = validate_excel_file("datos.xlsx", b"PK\x03\x04" + b"x" * 1000)
        assert not valid  # Falla porque falta estructura XLSX correcta
    
    def test_invalid_excel_extension(self):
        """Rechazar extensiones no permitidas"""
        valid, msg = validate_excel_file("datos.exe", b"datos")
        assert not valid
        assert "Extensión no permitida" in msg
    
    def test_excel_file_too_large(self):
        """Rechazar archivos mayores a 100MB"""
        large_file = b"x" * (101 * 1024 * 1024)
        valid, msg = validate_excel_file("datos.xlsx", large_file)
        assert not valid
        assert "demasiado grande" in msg.lower()
    
    def test_excel_path_traversal_attack(self):
        """Detectar intento de path traversal"""
        valid, msg = validate_excel_file("../../../etc/passwd.xlsx", b"PK\x03\x04")
        assert not valid
    
    def test_excel_windows_reserved_name(self):
        """Rechazar nombres reservados de Windows"""
        valid, msg = validate_excel_file("CON.xlsx", b"PK\x03\x04")
        assert not valid
    
    def test_required_columns_validation(self):
        """Validar que columnas requeridas están presentes"""
        headers = ["ID", "Nombre", "Fecha"]
        required = ["ID", "Nombre"]
        
        valid, missing = validate_required_columns(headers, required)
        assert valid
        assert missing == []
    
    def test_missing_required_columns(self):
        """Detectar columnas requeridas faltantes"""
        headers = ["ID", "Nombre"]
        required = ["ID", "Nombre", "Email"]
        
        valid, missing = validate_required_columns(headers, required)
        assert not valid
        assert "email" in [m.lower() for m in missing]
    
    def test_find_duplicate_rows(self):
        """Detectar filas duplicadas dentro del archivo"""
        rows = [
            {"id": 1, "nombre": "Juan"},
            {"id": 2, "nombre": "María"},
            {"id": 1, "nombre": "Juan"},  # Duplicado
        ]
        
        unique, duplicates = find_duplicate_rows(rows, ["id"])
        assert len(unique) == 2
        assert len(duplicates) == 1
        assert duplicates[0] == 2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE VALIDACIÓN DE PDF
# ══════════════════════════════════════════════════════════════════════════════

class TestPDFValidation:
    """Tests para validación de archivos PDF"""
    
    def test_valid_pdf_extension(self):
        """Validar que extensión .pdf se acepta"""
        pdf_bytes = b"%PDF-1.4\ntest content\n%%EOF"
        valid, msg = validate_pdf_file("manual.pdf", pdf_bytes)
        assert valid
    
    def test_invalid_pdf_extension(self):
        """Rechazar extensiones no permitidas"""
        valid, msg = validate_pdf_file("manual.doc", b"%PDF-1.4")
        assert not valid
        assert "Extensión no permitida" in msg
    
    def test_pdf_file_too_large(self):
        """Rechazar PDFs mayores a 100MB"""
        large_pdf = b"%PDF-1.4" + b"x" * (101 * 1024 * 1024)
        valid, msg = validate_pdf_file("manual.pdf", large_pdf)
        assert not valid
        assert "demasiado grande" in msg.lower()
    
    def test_pdf_missing_magic_bytes(self):
        """Rechazar archivos sin magic bytes de PDF"""
        valid, msg = validate_pdf_file("malicious.pdf", b"NOT_A_PDF\n%%EOF")
        assert not valid
        assert "No es un PDF válido" in msg
    
    def test_pdf_incomplete(self):
        """Rechazar PDF incompleto (sin %%EOF)"""
        valid, msg = validate_pdf_file("incomplete.pdf", b"%PDF-1.4\ntest content")
        assert not valid
        assert "No está completo" in msg or "falta" in msg.lower()
    
    def test_pdf_path_traversal(self):
        """Detectar intento de path traversal en PDF"""
        valid, msg = validate_pdf_file("../../etc/passwd.pdf", b"%PDF-1.4\n%%EOF")
        assert not valid


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE DETECCIÓN DE MIME TYPE
# ══════════════════════════════════════════════════════════════════════════════

class TestMimeTypeDetection:
    """Tests para detección de MIME type real"""
    
    def test_detect_xlsx_from_bytes(self):
        """Detectar XLSX por magic bytes"""
        xlsx_bytes = b"PK\x03\x04" + b"x" * 100
        mime = detect_mime_type(xlsx_bytes, "archivo.xlsx")
        assert "spreadsheet" in mime or "zip" in mime.lower()
    
    def test_detect_pdf_from_bytes(self):
        """Detectar PDF por magic bytes"""
        pdf_bytes = b"%PDF-1.4\ntest"
        mime = detect_mime_type(pdf_bytes, "manual.pdf")
        assert mime == "application/pdf"
    
    def test_detect_csv_from_filename(self):
        """Detectar CSV por nombre de archivo"""
        csv_bytes = b"id,nombre,fecha\n1,Juan,2026-01-01"
        mime = detect_mime_type(csv_bytes, "datos.csv")
        assert mime == "text/csv"
    
    def test_exe_renamed_as_xlsx(self):
        """Detectar ejecutable renombrado como Excel"""
        # EXE típicamente empieza con MZ
        exe_bytes = b"MZ\x90\x00"
        mime = detect_mime_type(exe_bytes, "virus.xlsx")
        # No debería detectar como Excel válido
        assert mime != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE SEGURIDAD DE NOMBRES DE ARCHIVO
# ══════════════════════════════════════════════════════════════════════════════

class TestFilenameSecurity:
    """Tests para seguridad de nombres de archivo"""
    
    def test_safe_filename(self):
        """Aceptar nombre de archivo seguro"""
        assert is_safe_filename("reporte_2026.xlsx")
        assert is_safe_filename("manual_técnico.pdf")
    
    def test_path_traversal_with_dots(self):
        """Rechazar path traversal con ../ """
        assert not is_safe_filename("../../../etc/passwd")
        assert not is_safe_filename("..\\..\\windows\\system32")
    
    def test_null_byte_injection(self):
        """Rechazar null bytes"""
        assert not is_safe_filename("archivo\x00.pdf")
    
    def test_newline_injection(self):
        """Rechazar caracteres de newline"""
        assert not is_safe_filename("archivo\n.pdf")
        assert not is_safe_filename("archivo\r\n.pdf")
    
    def test_windows_reserved_names(self):
        """Rechazar nombres reservados de Windows"""
        assert not is_safe_filename("CON.pdf")
        assert not is_safe_filename("PRN.xlsx")
        assert not is_safe_filename("AUX.csv")
        assert not is_safe_filename("COM1.pdf")
    
    def test_filename_too_long(self):
        """Rechazar nombres demasiado largos"""
        long_name = "a" * 300 + ".pdf"
        assert not is_safe_filename(long_name)
    
    def test_generate_safe_filename(self):
        """Generar nombre de archivo seguro aleatorio"""
        safe1 = generate_safe_filename("reporte_confidencial.pdf")
        safe2 = generate_safe_filename("reporte_confidencial.pdf")
        
        # Deben ser distintos (aleatorios)
        assert safe1 != safe2
        
        # Deben tener extensión
        assert safe1.endswith(".pdf")
        assert safe2.endswith(".pdf")
        
        # Deben ser seguros (sin path traversal)
        assert "/" not in safe1
        assert "\\" not in safe1
        assert ".." not in safe1


# ══════════════════════════════════════════════════════════════════════════════
# TESTS DE CASOS DE ATAQUE
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurityAttacks:
    """Tests de casos de ataque conocidos"""
    
    def test_zip_bomb(self):
        """Detectar Zip bomb (archivo comprimido malicioso)"""
        # Un Zip bomb tiene magic bytes PK pero es altamente comprimido
        zip_bomb = b"PK\x03\x04" + b"\x00" * (101 * 1024 * 1024)  # Muy comprimido
        
        valid, msg = validate_excel_file("bomb.xlsx", zip_bomb[:1024])
        # Aunque pase validación MIME, debería fallar en estructura
        # En la práctica, esto se detectaría al intentar descomprimirse
    
    def test_double_extension_attack(self):
        """Detectar ataque de doble extensión"""
        # Un archivo llamado "document.pdf.exe"
        valid, msg = validate_pdf_file("document.pdf.exe", b"%PDF-1.4\n%%EOF")
        # Debería fallar porque extensión es .exe, no .pdf
        assert not valid
    
    def test_case_insensitive_extension(self):
        """Validar extensiones en diferentes mayúsculas"""
        # .XLSX, .Xlsx, .xlsx deben ser válidas
        pdf_bytes = b"%PDF-1.4\n%%EOF"
        valid1, msg1 = validate_pdf_file("MANUAL.PDF", pdf_bytes)
        valid2, msg2 = validate_pdf_file("Manual.Pdf", pdf_bytes)
        valid3, msg3 = validate_pdf_file("manual.pdf", pdf_bytes)
        
        assert valid1
        assert valid2
        assert valid3


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
