@echo off

rem 编译 tcpingoo.py
call nuitka --mingw64 --onefile --output-dir=dist tcpingoo.py

rem 编译 udpingoo.py.py
call nuitka --mingw64 --onefile --output-dir=dist udpingoo.py

rem 编译 icmpingoo.py
call nuitka --mingw64 --onefile --output-dir=dist icmpingoo.py

echo 编译完成。
pause
