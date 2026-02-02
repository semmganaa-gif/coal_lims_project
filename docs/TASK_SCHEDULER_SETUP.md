# Windows Task Scheduler - Автомат Backup Тохиргоо

LIMS системийн өдөр тутмын автомат backup хийх заавар.

## 1. Task Scheduler нээх

```
Win + R → taskschd.msc → Enter
```

Эсвэл: Start → "Task Scheduler" хайх

## 2. Шинэ Task үүсгэх

### 2.1 Basic Task Wizard ашиглах

1. **Action** цэснээс → **Create Basic Task...**
2. **Name**: `LIMS Daily Backup`
3. **Description**: `PostgreSQL database backup every day at 2:00 AM`
4. **Next** дарах

### 2.2 Trigger (Хэзээ ажиллах)

1. **Daily** сонгох → **Next**
2. **Start**: Өнөөдрийн огноо
3. **Time**: `2:00:00 AM` (шөнийн 2 цаг - серверт ачаалал багатай үед)
4. **Recur every**: `1` days
5. **Next** дарах

### 2.3 Action (Юу хийх)

1. **Start a program** сонгох → **Next**
2. **Program/script**:
   ```
   D:\coal_lims_project\scripts\scheduled_backup.bat
   ```
3. **Start in** (optional):
   ```
   D:\coal_lims_project
   ```
4. **Next** дарах

### 2.4 Finish

1. **Open the Properties dialog...** checkbox тэмдэглэх
2. **Finish** дарах

## 3. Нэмэлт тохиргоо (Properties)

### 3.1 General tab

- **Run whether user is logged on or not** - сонгох
- **Run with highest privileges** - тэмдэглэх
- **Configure for**: Windows 10 эсвэл Windows Server 2019

### 3.2 Conditions tab

- **Start the task only if the computer is on AC power** - арилгах
- **Wake the computer to run this task** - тэмдэглэх (optional)

### 3.3 Settings tab

- **Allow task to be run on demand** - тэмдэглэх
- **Run task as soon as possible after a scheduled start is missed** - тэмдэглэх
- **If the task fails, restart every**: 10 minutes, **Attempt to restart up to**: 3 times
- **Stop the task if it runs longer than**: 1 hour

## 4. Гараар тест хийх

Task Scheduler дээр:
1. `LIMS Daily Backup` task дээр right-click
2. **Run** сонгох
3. `D:\coal_lims_project\backups\` хавтаст backup файл үүссэн эсэхийг шалгах

## 5. Command Line-аас үүсгэх (Alternative)

PowerShell-д (Administrator):

```powershell
# Task үүсгэх
$action = New-ScheduledTaskAction -Execute "D:\coal_lims_project\scripts\scheduled_backup.bat" -WorkingDirectory "D:\coal_lims_project"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "LIMS Daily Backup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "PostgreSQL database backup every day at 2:00 AM"
```

## 6. Backup файлуудын байршил

```
D:\coal_lims_project\backups\
├── lims_20251218_020000.sql      # PostgreSQL dump
├── lims_20251217_020000.sql
├── lims_20251216_020000.sql
└── ... (сүүлийн 30 хоногийн backup)
```

## 7. Log шалгах

Backup script-ийн log:
```
D:\coal_lims_project\logs\backup.log
```

Task Scheduler history:
1. Task Scheduler → LIMS Daily Backup
2. **History** tab дээр дарах
3. Run result шалгах

## 8. Алдаа засах

### Task ажиллахгүй бол:

1. **Path шалгах**: `D:\coal_lims_project\scripts\scheduled_backup.bat` файл байгаа эсэх
2. **PostgreSQL**: `pg_dump` PATH-д байгаа эсэх
3. **Permissions**: SYSTEM user-д backup хавтаст бичих эрх байгаа эсэх

### PostgreSQL алдаа:

```batch
REM pg_dump PATH-д нэмэх
set PATH=%PATH%;C:\Program Files\PostgreSQL\18\bin
```

### Permission алдаа:

```batch
REM backups хавтасны эрх шалгах
icacls D:\coal_lims_project\backups
```

## 9. Email мэдэгдэл (Optional)

Backup амжилттай/амжилтгүй болсон тухай email илгээх:

`scripts/scheduled_backup.bat` файлд нэмэх:

```batch
REM Email илгээх (PowerShell ашиглан)
if %ERRORLEVEL% EQU 0 (
    powershell -Command "Send-MailMessage -To 'admin@example.com' -From 'backup@example.com' -Subject 'LIMS Backup Success' -Body 'Daily backup completed successfully.' -SmtpServer 'smtp.example.com'"
) else (
    powershell -Command "Send-MailMessage -To 'admin@example.com' -From 'backup@example.com' -Subject 'LIMS Backup FAILED' -Body 'Daily backup failed! Please check logs.' -SmtpServer 'smtp.example.com' -Priority High"
)
```

## 10. Checklist

- [ ] Task Scheduler-д task үүсгэсэн
- [ ] Гараар тест хийж backup файл үүссэн
- [ ] Run whether user is logged on or not тохируулсан
- [ ] History-д амжилттай run харагдаж байгаа
- [ ] 30 хоногийн дараа хуучин backup автоматаар устаж байгаа
