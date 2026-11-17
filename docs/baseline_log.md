# Baseline Log (Week 1)

**My decision:** Which construction machines need maintenance this week based on their operating hours?

**How often I make it:** My dad receives hour-meter readings daily. He records and reviews them every day, or every two to three days when he is busy. I still need to confirm how often he checks which machines are due for maintenance. My goal is to help him make that check every week.

**Current process:** My dad runs a construction equipment business in Manizales, Colombia, with six machines and six operators. The operators send photos of the hour meters or write down the readings. My dad records the readings in a notebook and then enters them into Excel. He spends about eight hours a week recording and reviewing this information. Sometimes oil changes are missed because it is hard to keep track of each machine’s operating hours.

Log each decision **while it happens**. Time yourself with a timer; don't estimate afterward.
Mark any entry you had to reconstruct from memory as *(reconstructed)*.

| Date | What I was deciding | What I looked at | Time (min) | What I wished I knew | Confidence (1–5) | Reconstructed? |
|---|---|---|---|---|---|---|
| Not Recalled  | Understanding how my dad keeps track of machine hours | I talked to  my dad on the phone, and he sent me pictures of his notebooks | Not recorded  | How to find the latest hours for each machine more easily, since everything was handwritten on different pages | 4 | Yes  |
| Not recalled | Deciding whether to use Pasto data for my project | I looked at the API results from Manizales and Pasto | Not recorded | I wanted to know if we could find data from Manizales that would actually help my dad's business | 2 | Yes |
| Not recalled | Checking if the downloaded data was useful for my project | I looked at the 500 land records and 1,218 building records from Pasto | Not recorded | How data from another city could help my dad's business in Manizales | 3 | Yes |
| Not recalled | Deciding whether to approve Codex commands | I reviewed the commands and asked ChatGPT to explain them before approving | Not recorded | I wanted to understand what each command would do | 5 | Yes |
| Not recalled | Finding an API with useful data from Manizales | I looked at the Manizales API and other data options, including weather data | Not recorded | I wanted to know which API would work for my project and provide useful information | 3 | Yes |
| 2026-11-10 | Whether the CAT 312E excavator might need an oil change soon. | A conversation with my dad, photos of his handwritten maintenance records, and the machine's hour-meter readings. | Our call lasted 23 minutes, but I did not separately time the maintenance decision. | How often the oil needs to be changed so I could determine when the next maintenance is due. |   3, unsure about the next oil change.| No — the review happened that day, although the decision time was not measured.|

## Reflection

1. **The three most frustrating or time-consuming parts:** Entering the same information by hand, following up when readings arrive late, and keeping track of when each machine needs an oil change.
2. **What would make me trust a system's recommendation? What would make me ignore it?** I would trust a recommendation if it uses accurate hour-meter readings and shows the machine’s maintenance history. I would set it aside if I couldn’t verify the reading or see that history.
3. **What a system should never do on my behalf without asking:** It should ask for confirmation before deleting information, changing records, or marking maintenance as completed.
4. **How I would know it was actually helping** (this becomes my value hypothesis): My dad would spend less time entering and reviewing records, and fewer oil changes would become overdue.
5. **One assumption about my own workflow that this log proved wrong:** I thought finding useful data from Manizales would be easier, but I learned that not every API works or has the information I need for my project.

**Project scope:** The first version will let operators submit hour-meter readings through a website. My dad will be able to see each machine’s operating hours, who is assigned to it, and when it needs an oil change. Later, the website could show which machines are available or working, the estimated completion date for each job, and how each job is progressing.
