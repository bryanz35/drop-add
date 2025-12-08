# NCSSM Drop Add 2023-2024

- Students with requests: 370
- Students to process: 233

Current edges cases:

- Ignore M block.
- Ignore requests with no drop and "None of these apply".
  Overloading will be processed after (lowest priority).
- Ignore requests with no add and "None of these apply".
  Underloading will be processed after (lowest priority).
- Mentorship 3080 doesn't exist in schedules and has weird ID problems.
- MA1012-002 doesn't appear in offerings list.
- If someone puts no main but alts, bump first alt to main.
- Ignore courses that appear in requests but not offerings.
  - HU4410
  - CS4120
  - HU4480
- Ignore requests that deal with AS4052 (Amstud II)
- Ignore requests that drops course student does not have (S535, S592).
- Delete add alternates if it is the same as the drop
  (why would you request to drop and add the same course).
- If a course has more people enrolled than its cap before drop add,
  we set the new cap to be the number of enrollments.

Limitations:

- We compute the drop add for ones without additional constraints.
  However, the ones with constraints should be done first and given priority.
  This means some requests that shouldn't be fulfilled are granted,
  and some requests that could be fulfilled aren't.
