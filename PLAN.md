# alanknguyen.com: content and build plan

Date: 2026-10-06. Inspirations: jonbarron.info, jessezhang.net.

## 1. Where things stand

The folder already holds a draft from March 2026: six hand-written pages (index, research, projects, teaching, blog, resume), one stylesheet, a theme toggle, and a Python http.server preview config.

- Layout is a 320px sticky sidebar plus cards, in Montserrat. That is a portfolio look, not the narrow single-column academic look of the two inspirations.
- The photo is a via.placeholder.com image, the Scholar link points at scholar.google.com with no profile, and the CV link has no PDF behind it.
- Research and Projects pages repeat the same five cards with "TLDR" blurbs. There is no publication list with real PDFs yet.
- Blog is a "coming soon" page.
- The folder has no git repository of its own. It sits untracked inside the Clanq repository that lives in your home folder. Give it its own repo before publishing (you run git init, add the remote, and push).

Prototype built 2026-10-06: index.html, css/site.css, js/site.js, demo thumbnails in img/thumbs/. The March pages and their CSS/JS moved to legacy/.

Worth keeping from the old draft: the CSS variable scheme with light and dark tokens, the mobile breakpoints, and the facts in resume.html (dates, roles, coursework, skills). Everything else gets rewritten.

## 2. What the inspirations do, and what to take

jonbarron.info: one page. Name top-left, photo top-right, a four-sentence bio, a link row (email, CV, bio, Scholar, Twitter, GitHub). Then a research table: thumbnail on the left; title, authors, venue, link row, and a one-line caption on the right. Then micropapers, talks, service, teaching, and a footer that invites people to reuse the HTML. Black text on white, narrow column, almost no CSS.

jessezhang.net: same header, then News (dated one-liners), Research with a Highlighted/All toggle, Blog posts, Service, Teaching, Invited Talks.

Take: the header and bio shape, the link row, the thumbnail table, the News list, the narrow column, the restraint. Adapt: your research list is short, so Notes and Projects become first-class sections with the same thumbnail-table treatment instead of an afterthought.

## 3. Positioning and voice

- Who you are on the page: Alan Nguyen (Nguyen Khoi Nguyen), M.S. student in ECE, Systems Robotics, Boston University, working on embodied AI at the Dependable Computing Lab. B.A. Physics and Computer Science, BU, Dec 2025. Earlier research in computational optics and photonics with Luca Dal Negro and Lei Tian. Co-founder of the BU AI Society.
- Voice: first person, plain declarative sentences, specific nouns. No "passionate", no "cutting-edge", no "leveraging". The bio says what you work on, with whom, what you did before, and what the site contains.
- Listing rule: the Research section lists only things a visitor can open (PDF, preprint, report, code). Work in progress is a sentence in the bio or a News line, never a research entry.
- Author lists: write the real names. Use "et al." only for long lists.
- Remove dead links: Scholar until a profile with entries exists, Blog until a post exists.
- Photo: a real one, roughly square, about 400px, before anything goes live.

## 4. Site map

```
/                         Home: header, bio, news, research (all), selected projects,
                          selected notes, teaching (short), service, footer
/research/                Every report and preprint, thumbnail table
/projects/                Every project, thumbnail table
/projects/<slug>/         One page per project
/notes/                   Index grouped by course
/notes/<course>/          Course landing: what it is, when taken, list of topics, PDF
/notes/<course>/<topic>/  One topic page (Markdown, KaTeX math, figures)
/reviews/                 Paper reviews, grouped by series
/reviews/<slug>/          One review
/teaching/                Courses taught or TA'd, BUAIS lectures
/files/cv.pdf             CV
/files/...                Report PDFs, note PDFs
```

Home carries the full research list because it is short. Projects and Notes on the home page are curated subsets with "all projects" and "all notes" links.

## 5. Page specs

### Home

1. Header: name as h1; photo top-right (160 to 200px); one line under the name ("M.S. student, ECE, Boston University"); link row: Email, CV, GitHub, LinkedIn.
2. Bio: 4 to 6 sentences (draft in section 8).
3. News: 6 to 10 lines, newest first, "Mon YYYY" then the fact. Trim anything older than two years once the list grows.
4. Research: every entry has a thumbnail (a figure from the report, 4:3, about 400px wide), a title linking to the PDF, authors with you in bold, a type line ("Technical report, BU ECE, 2025" or "Preprint, 2026"), a link row (PDF, code, project page, notes), and one sentence saying what the result is.
5. Projects: one line saying write-ups are coming soon (your call, 2026-10-06). Once ready: same row format as research, title linking to the project page.
6. Notes (selected, 3 to 5): course code and name, one line on scope, link to the course landing.
7. Teaching: three or four lines, link to /teaching/.
8. Service and community: BUAIS in two lines.
9. Footer: year, and a credit line if you reuse Barron's HTML (he asks for one).

### Project page (template)

Title. One-line subtitle. Date range. Role and collaborators. Teaser figure or GIF.

- Summary: three to five sentences, the result first.
- Problem and constraints.
- Design or method, with one diagram.
- Results: measured numbers, plots, a video or GIF.
- What I would change.
- Links: code, report PDF, related notes.

Engineering projects (FPGA, simulators) get a "hardware and tools" line. Research-flavored ones get a BibTeX block if a report exists.

### Notes

Course landing: course code and name, semester taken, instructor, textbook, what the notes cover and what they skip, a list of topic pages in syllabus order, one PDF of the whole set.

Topic page: title, prerequisites (links to other topics), the notes themselves with numbered equations and figures, a short "where this is used" paragraph, references. Math in KaTeX. One source file per topic.

Discussion notes (recitation or discussion-section write-ups) live under the same course with a "Discussion N" prefix.

### Paper review (template)

Paper title, authors, venue, year, links. Then: one-paragraph summary; the key idea in one or two sentences; method; results that matter; limitations and what I would test; how it relates to my work; a short "read this if" line.

Group reviews into series (for example "Imitation learning for driving") with a series page that orders them and says what the series is for.

### Teaching

One block per course: code, name, role, term, one paragraph, links to materials you are allowed to post. Then the BUAIS lecture series as a list with dates and slide links.

## 6. Content inventory

Confirmed from the current pages:

| Item | Type | Destination | Needs |
|---|---|---|---|
| Quantum states of light in cavity QED (Dal Negro, 2024 to 2025) | report | /research/ | PDF, one figure, final title and date |
| Intensity diffraction tomography forward models (Tian, 2025) | report | /research/ | PDF, one figure |
| FEM for metasurfaces and plasmonics (Dal Negro, 2024) | report or project | /research/ or /projects/ | decide which; PDF or code |
| Sawyer VLM/VLA manipulation stack (DCL, 2025 onward) | project | /projects/sawyer-vla/ | GIF of the arm, architecture diagram, repo link if public |
| GreenMetric.ai | project | /projects/greenmetric/ | screenshot; keep it short |
| BU AI Society | service | home, /teaching/ | dates, links |
| CS 185 Systems-First Machine Vision (BUAIS, Spring 2026) | teaching | /teaching/ | syllabus, slides you can share |
| EC574 and EC575 TA (semiconductor sequence) | teaching | /teaching/ | recitation notes become /notes/ec574/ discussion pages |

Candidates seen only as folder or file names on your Desktop (not opened; confirm each):

| Folder or file | Likely page |
|---|---|
| DE10-Lite manuals, Nios II PDF, LaMeres VHDL labs | /projects/cnn-on-fpga/ |
| optics_app, computational-optics-laboratory (Downloads) | /projects/optics-simulator/ (one page per simulator if they differ) |
| stereo_vision_tracker | /projects/stereo-tracker/ |
| ZedMiniWristMount | /projects/zed-wrist-mount/ (hardware, short) |
| qsol_cqed, qsol_cqed_figures | figures for the CQED research entry, or a small project page |
| Teacher_Student_Driving decks; UAVControlDagger2013, EndtoEndNVIDIAcar2016, ExplainEnd2EndNVIDIA2017, ConditionalImitationLearning2018, DeepImitation2018, QueryEnd2EndRL, ImitationLearningtoOnlineLearning PDFs | /reviews/ series "Imitation learning for driving", plus /projects/teacher-student-driving/ |
| Principles of Robot Autonomy.pdf | /notes/ course, if these are your notes |
| cpp-notes | /notes/cpp/ |
| Coursework in resume.html: ML, Deep Learning, Image and Video Computing, Electromagnetics, Cyber-Physical Systems, Optimal and Robust Control, Embedded Systems | one /notes/<course>/ each, as material exists |

## 7. Tech plan

Recommendation: Astro, static output, deployed to GitHub Pages or Cloudflare Pages under alanknguyen.com.

- Why not stay with hand-written HTML: six pages are fine by hand; thirty note pages with equations are not. Markdown plus KaTeX (remark-math and rehype-katex) is the right unit of work for notes and reviews.
- Why Astro over Hugo or Jekyll: content collections give typed front matter for projects, notes, and reviews; the home page stays a hand-written template; you already work in JavaScript and React. Hugo is the alternative if you want a single binary and no node_modules.
- Styling: one stylesheet, column about 720px, a system or serif font stack, keep the current light and dark tokens. Port the breakpoints from css/style.css. Drop the sidebar.
- Images: thumbnails as WebP at 2x; simulators as short GIF or MP4 loops; figures as SVG or PNG.
- PDFs under /files/. Optional: build each course's note set into a PDF with Pandoc from the same Markdown.
- Metadata: title and description per page, OpenGraph image, favicon, sitemap, RSS for notes and reviews.
- Domain: CNAME file in the repo; A and AAAA records (GitHub Pages) or a CNAME record (Cloudflare Pages) at your registrar.
- Repo hygiene: own repository for the site, not the Clanq repo in your home folder. You run every git command.

## 8. Drafts to start from

Everything in brackets needs your confirmation or a fact I do not have.

Bio:

> I am a master's student in Electrical and Computer Engineering (Systems Robotics) at Boston University, where I work on embodied AI in the Dependable Computing Lab [with NAME]. My current work is a perception-to-action stack for a 7-DoF Sawyer arm: vision-language models for grounding, ROS 2 for execution, and Isaac Sim for sim-to-real transfer. Before this I completed a B.A. in Physics and Computer Science at BU (2025), with research in computational optics: quantum states of light in cavity QED with Luca Dal Negro, intensity diffraction tomography with Lei Tian, and finite-element simulation of metasurfaces. I co-founded the BU AI Society and taught its Systems-First Machine Vision course. This site collects my reports, project write-ups, paper reviews, and course notes.

News (newest first; drop any that are no longer true):

- Sep 2026: Started the M.S. in ECE (Systems Robotics) at Boston University.
- Spring 2026: Taught CS 185, Systems-First Machine Vision, through the BU AI Society.
- Dec 2025: Completed the B.A. in Physics and Computer Science at BU.
- Sep 2025: Joined the Dependable Computing Lab as an embodied AI researcher.
- Apr 2025: ML internship at Scale AI (computational physics and code reasoning), through Aug 2025.
- Feb 2025: Launched GreenMetric.ai.

Research entry (shape; fill from the report):

> **Theory and Applications of Quantum States of Light in Cavity QED Systems**
> Nguyen K. Nguyen. Advised by Luca Dal Negro.
> Technical report, Boston University, 2025. [confirm year]
> PDF / notes / code
> Operator-based formulations of cavity-mediated light-matter interaction, with [the specific model or result the report ends on].

Project page front matter:

```yaml
title: "CNN inference on a DE10-Lite FPGA"
subtitle: "[one line: what network, what throughput]"
dates: "[Mon YYYY to Mon YYYY]"
role: "Solo"
tags: [fpga, vhdl, cnn, embedded]
thumbnail: /img/projects/cnn-fpga.webp
links:
  code: "[repo URL]"
  report: /files/cnn-fpga-report.pdf
```

Notes topic page front matter:

```yaml
course: ec574
title: "Carrier transport: drift, diffusion, and the continuity equation"
order: 3
updated: 2026-10-06
```

## 9. Build order

1. Home page only, live on the domain. Real photo, bio, news, link row, research entries with real PDFs, CV PDF. One correct page beats six empty ones.
2. Project pages when you are ready to publish them (CNN on FPGA, the optics simulator, Sawyer VLA), each with a teaser GIF or figure. Until then the Projects section stays one line.
3. One course of notes end to end: landing page plus three to five topic pages. This fixes the math, figure, and cross-link conventions. Then batch the remaining courses.
4. The imitation-learning review series, five to seven reviews in one batch, with the series page.
5. Polish: remaining projects, Scholar link once the profile has entries, RSS, OpenGraph, blog if and when there is a post.

## 10. Questions for you

Nothing here blocks step 1 except the photo and the PDFs.

1. Which of the three research items have a finished PDF? Exact titles and dates as they should appear?
2. Who do you work with at DCL, and should the bio name them?
3. Which courses do you have notes for, and in what form (LaTeX, Markdown, handwritten PDF, Notion, Obsidian)? This decides the conversion path.
4. Astro (recommended), Hugo, or keep plain HTML plus a small build script?
5. Switch to the single-column layout (recommended) or keep the sidebar?
6. Hosting: GitHub Pages or Cloudflare Pages? Where is the domain registered?
