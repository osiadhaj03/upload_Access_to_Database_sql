#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقارنة طرق استخراج البيانات من ملفات .bok
"""

import os
import sys

def test_all_methods():
    """اختبار جميع الطرق المتاحة"""
    
    bok_file = r"d:\test3\bok file\بغية السائل.bok"
    
    print("🔍 اختبار طرق استخراج البيانات من ملفات .bok")
    print("=" * 60)
    
    methods = [
        ("1. pyodbc مع ODBC", test_pyodbc),
        ("2. Simple BOK Support", test_simple_bok),
        ("3. mdb-tools (Linux style)", test_mdb_tools),
        ("4. Python Access readers", test_python_access),
        ("5. CSV Export من Access", test_csv_export),
        ("6. PowerShell Access", test_powershell_access)
    ]
    
    for method_name, test_func in methods:
        print(f"\n{method_name}:")
        print("-" * 40)
        try:
            result = test_func(bok_file)
            if result:
                print(f"✅ {method_name}: نجح!")
            else:
                print(f"❌ {method_name}: فشل")
        except Exception as e:
            print(f"❌ {method_name}: خطأ - {str(e)}")

def test_pyodbc(bok_file):
    """اختبار pyodbc"""
    try:
        import pyodbc
        
        # جرب عدة connection strings
        connection_strings = [
            f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={bok_file};",
            f"DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={bok_file};",
            f"Provider=Microsoft.ACE.OLEDB.12.0;Data Source={bok_file};",
            f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={bok_file};"
        ]
        
        for i, conn_str in enumerate(connection_strings, 1):
            try:
                print(f"  تجربة {i}: {conn_str[:50]}...")
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM MSysObjects WHERE type=1")
                tables = cursor.fetchall()
                print(f"    ✅ وُجد {len(tables)} جدول")
                conn.close()
                return True
            except Exception as e:
                print(f"    ❌ فشل: {str(e)[:100]}...")
                
        return False
        
    except ImportError:
        print("  ❌ pyodbc غير مثبت")
        return False

def test_simple_bok(bok_file):
    """اختبار Simple BOK Support"""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        from simple_bok_support import SimpleBokProcessor
        
        processor = SimpleBokProcessor()
        result = processor.extract_from_bok(bok_file)
        
        if result and 'content_data' in result:
            content_count = len(result['content_data'])
            index_count = len(result.get('index_data', []))
            print(f"  ✅ استخرج {content_count} صفحة محتوى و {index_count} فهرس")
            return True
        else:
            print("  ❌ لم يستخرج بيانات صالحة")
            return False
            
    except Exception as e:
        print(f"  ❌ خطأ: {str(e)}")
        return False

def test_mdb_tools(bok_file):
    """اختبار mdb-tools (يحتاج WSL أو Linux)"""
    try:
        import subprocess
        
        # التحقق من وجود mdb-tools
        result = subprocess.run(['mdb-tables', bok_file], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            tables = result.stdout.strip().split()
            print(f"  ✅ وُجد {len(tables)} جدول: {', '.join(tables[:3])}...")
            return True
        else:
            print(f"  ❌ فشل: {result.stderr}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ❌ mdb-tools غير متوفر")
        return False

def test_python_access(bok_file):
    """اختبار مكتبات Python المتخصصة"""
    libraries = ['msaccessdb', 'pyjetdb', 'access_parser']
    
    for lib in libraries:
        try:
            if lib == 'msaccessdb':
                import msaccessdb
                db = msaccessdb.read(bok_file)
                tables = list(db.tables.keys())
                print(f"  ✅ {lib}: وُجد {len(tables)} جدول")
                return True
                
        except ImportError:
            print(f"  ❌ {lib}: غير مثبت")
        except Exception as e:
            print(f"  ❌ {lib}: خطأ - {str(e)[:50]}...")
    
    return False

def test_csv_export(bok_file):
    """اختبار تصدير CSV من Access"""
    print("  💡 يتطلب فتح Access يدوياً وتصدير البيانات كـ CSV")
    print("  📁 الجداول المطلوبة: Main, TBMain (للمحتوى), TBTitles (للفهرس)")
    return None

def test_powershell_access(bok_file):
    """اختبار PowerShell مع COM Objects"""
    try:
        ps_script = f'''
        $accessApp = New-Object -ComObject Access.Application
        $db = $accessApp.OpenCurrentDatabase("{bok_file}")
        $tables = $accessApp.CurrentDb().TableDefs | Where-Object {{ $_.Name -notlike "MSys*" }}
        $tableCount = $tables.Count
        $accessApp.Quit()
        Write-Output $tableCount
        '''
        
        import subprocess
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            table_count = result.stdout.strip()
            print(f"  ✅ PowerShell: وُجد {table_count} جدول")
            return True
        else:
            print(f"  ❌ PowerShell فشل: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ PowerShell خطأ: {str(e)}")
        return False

if __name__ == "__main__":
    test_all_methods()
    
    print("\n" + "=" * 60)
    print("🎯 التوصيات:")
    print("1. إذا نجح Simple BOK Support -> استخدمه")
    print("2. إذا نجح pyodbc -> حل مشكلة ODBC drivers") 
    print("3. إذا نجح PowerShell -> استخدم COM Objects")
    print("4. كحل أخير: تصدير يدوي لـ CSV من Access")
    
    input("\nاضغط Enter للخروج...")
