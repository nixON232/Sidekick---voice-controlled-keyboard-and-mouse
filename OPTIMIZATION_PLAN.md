# Sidekick Latency Optimization Plan

**Дата:** 11.01.2026
**Цель:** Сократить задержку выполнения команды "table N" с ~1.5-2 секунд до <1 секунды

---

## Текущее состояние

### Workflow команды "table N":
```
Произнесение "table N" → Аудио буфер (125-250мс) → Vosk STT (30-100мс) 
→ Parser (~1мс) → moveMouseTo (500мс анимация)
Общая задержка: ~700-900мс без учёта времени распознавания
```

---

## Планируемые оптимизации

### 1. Уменьшить аудио буфер (sidekick.py:105)

**Текущее значение:**
```python
data = stream.read(4000, exception_on_overflow = False)  # 4000 байт = 250мс
```

**Новое значение:**
```python
data = stream.read(2000, exception_on_overflow = False)  # 2000 байт = 125мс
```

**Эффект:** Частота итераций основного цикла удваивается, снижая latency на 50-125мс

---

### 2. Снизить waittime threshold (sidekick.py:128)

**Текущее значение:**
```python
if waittime >= 8:  # ~2 секунды post-speech буферизации
    wait = False
```

**Новое значение:**
```python
if waittime >= 5:  # ~1.25 секунды post-speech буферизации
    wait = False
```

**Эффект:** Сокращение времени ожидания после окончания речи на 40% (~750мс)

---

### 3. Оптимизировать вызов KaldiRecognizer (sidekick.py:131-149)

**Текущее состояние:**
```python
trec = textrec.AcceptWaveform(data)   # Вызывается всегда
crec = commandrec.AcceptWaveform(data) # Вызывается всегда
arec = alpharec.AcceptWaveform(data)   # Вызывается всегда
```

**Проблема:** Три вызова `AcceptWaveform()` на каждый аудио буфер

**Оптимизация:**
```python
if parser.state == "text":
    trec = textrec.AcceptWaveform(data)
elif parser.state == "alpha":
    arec = alpharec.AcceptWaveform(data)
else:  # command или mouse
    crec = commandrec.AcceptWaveform(data)
```

**Эффект:** -66% вычислительной нагрузки на STT

---

### 4. Добавить DEBUG флаг для отладочного вывода (parser.py)

**Текущее состояние:**
```python
def evaluate(self):
    ...
    print(self.command_buffer)  # Блокирующий I/O
```

**Оптимизация:**
```python
DEBUG = False  # Изменить на True для отладки

def evaluate(self):
    ...
    if DEBUG:
        print(self.command_buffer)
```

**Эффект:** Устранение блокирующего вывода в production

---

### 5. Условный print в sidekick.py

**Текущее:** print команд всегда выполняется

**Оптимизация:** Обернуть в DEBUG проверку или убрать в production

---

## Ограничения (по требованиям пользователя)

1. **Модель:** Оставить текущую vosk-model-en-us-daanzu-20200905-lgraph (129MB)
2. **Анимация мыши:** Сохранить 0.5 секунды на moveMouseTo
3. **Баланс:** Максимальная скорость без смены модели

---

## Ожидаемый результат

| Параметр | До | После |
|----------|-----|-------|
| Аудио буфер | 250мс | 125мс |
| Post-speech буфер | 2000мс | 1250мс |
| STT вызовы | 3x/цикл | 1x/цикл |
| Print I/O | Да | Нет (production) |
| **Общая задержка** | **~1500-2000мс** | **~700-900мс** |

---

## Файлы для изменения

1. `sidekick.py` - строки 105, 128, 131-149, добавить DEBUG
2. `parsepackage/parser.py` - строка 81-82, добавить DEBUG флаг

---

## Тестирование

После изменений проверить:
1. Корректность распознавания команд "table 1" - "table 9"
2. Отсутствие ложных срабатываний
3. Время от произнесения до реакции (субъективно)
4. Стабильность работы при фоновом шуме
