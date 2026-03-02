# Writing Effective Job Stories

## Why job stories over user stories

User stories ("As a [role], I want [feature], so that [benefit]") anchor on
the role, which often leads to generic features. Job stories anchor on the
**situation** and **motivation**, which produces more specific, useful
requirements.

## Format

**When** [situation/context], **I want to** [motivation/action], **so I can** [expected outcome].

## Good job stories

The situation should be specific enough that you can picture the moment:

- **JS-001**: When I have a sudden idea while doing something else, I want to
  capture it without opening an app, so I can stay in flow and not lose my
  train of thought.

- **JS-006**: When I mention a project name while speaking my idea, I want the
  app to automatically file it there, so my ideas are organized without extra
  steps.

- **JS-012**: When I'm reviewing an idea, I want to see both the text and hear
  the original audio, so I can catch nuances lost in transcription.

## What makes them good

1. **Specific situation** — "while doing something else", "while speaking my
   idea", "reviewing an idea". You can picture the exact moment.

2. **Clear motivation** — not a feature request ("I want a button"), but a
   human need ("I want to capture it without opening an app").

3. **Outcome connects to a real goal** — "stay in flow", "organized without
   extra steps", "catch nuances".

## Bad job stories (and fixes)

**Bad**: When I use the app, I want it to work well, so I have a good experience.
→ Too vague. What situation? What does "work well" mean?

**Fix**: When I'm in a meeting and can't speak, I want to type my idea instead
of speaking, so I never lose ideas due to my environment.

**Bad**: As a user, I want to save ideas.
→ This is a user story, not a job story. No situation, no motivation.

**Fix**: When I'm offline with no internet, I want the app to save my idea
locally, so connectivity doesn't become a barrier to capturing thoughts.

## Numbering convention

Use a prefix + sequential number: JS-001, JS-002, etc. Group related stories
under theme headers (Capture, Organization, Review, etc.). This numbering lets
RFCs reference specific stories for traceability.

## Coverage check

After writing all job stories, verify:

- Every user persona has at least 2-3 job stories
- Every MVP feature maps to at least one job story
- Edge cases are covered (offline, errors, permissions)
- The "unhappy paths" are represented (mis-categorization, transcription failure)
