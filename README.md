# pyBot
**1. nonActivitiesHelpers.py** — удаление неактивных более N дней помощников новичков<br>
**2. checkLinksThere.py** — проверка корректности установки номинационных шаблонов<br>
**3. trashCheck.py** — мониторинг свежих правок на предмет наличие в них феминитивных слов-уродов, таких как «авторка»<br>

Все скрипты писались для выполнения конкретных задач и по принципу «абы работало».
Сей говнокод предоставляется по принципу «как есть». Критика игнорируется полностью, хотя замечания
и предложения по функционалу, выраженные в адекватной форме, приветствуются.

**Список задач на будущее [которое не наступит]:**
1. В скрипте мониторинга шаблонов избавиться от временного файла с отчётом.
2. В скрипте мониторинга шаблонов реализовать уведомление о наличии нескольких целевых шаблонов
на одной странице, чтобы костыль с nowiki выглядел не настолько дико.
3. В скрипте мониторинга активности помощников обработать случаи переименованной учётной записи и, возможно,
бессрочных блокировок.
4. В скрипте мониторинга феминитивов обработать случаи добавления феминитива с фрагментами викиразметки (автор]]ка).
5. В скрипте мониторинга феминитивов сделать при каждой проходке проверку на актуальность отчётной страницы (наличие
феминитивов в текущей версии) и удаление потерявших актуальность строк.
