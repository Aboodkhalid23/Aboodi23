# Social Media Account Investigation

For investigating who is behind a social media account, whether the account is authentic, and what its behavioural patterns are

## When to read this file

Read when the journalist asks:

- "Who is behind this account?"
- "Is this a bot?"
- "Is this account part of a coordinated campaign?"
- "Investigar essa conta no Twitter / Instagram / TikTok"

This file overlaps with the existing `social-media-intelligence` skill (which focuses on narrative tracking and viral spread). When in doubt, both can be consulted — they are complementary.

## The four questions

Every account investigation answers four questions, in this order.

### 1. Identity — who is the human behind the account?

- What name does the account use? Is it consistent across platforms?
- What handle / username? Has it changed? (Wayback Machine on the profile page can show prior names.)
- What email or phone is associated, if any are publicly visible (rare on most platforms; sometimes leaked via password-reset behaviour, but **do not exploit password-reset flows for an investigation** — that crosses an ethical line).
- Is this a real person, a persona, an organisation, or a bot?

Tools: **Sherlock**, **WhatsMyName**, **Maigret** for username re-use across platforms (check whether the same handle exists on 100+ services). **Epieos** / **Holehe** for free-tier email-presence checks (input an email, see which services say "this email is registered"). Use these only on accounts that are already in the public eye for a journalistic reason.

### 2. Authenticity — is the account genuine?

Signals of inauthenticity (any one is suggestive; several together is conclusive):

- **Recent creation date** + **immediate high posting volume** — suggests a manufactured account, especially if it started right before a campaign
- **Stock-photo profile picture** — reverse-search the avatar on Yandex / Google Lens
- **AI-generated profile picture** — look for the artefacts listed in `verification-checklist.md` (asymmetric eyes, weird ears, glasses inconsistencies)
- **Display name / handle mismatch** — "John Smith" with handle `@asd2837481`
- **Posting patterns inconsistent with claimed identity** — a "small-town American homemaker" who posts in idiomatic Russian
- **Engagement patterns** — high follower count with very low engagement-per-post (purchased followers); or extremely high engagement only from accounts that also look fake (mutual amplification)
- **Identical or near-identical content** across multiple accounts at near-identical times — coordinated inauthentic behaviour
- **Bio/description copy-pasted** from a known template

**Important distinction:** "Bot" and "inauthentic" are not the same. A real human running a fake persona is inauthentic but not a bot. A real human who tweets a lot is neither. Be precise.

### 3. Network — what is the account connected to?

- **Who do they follow, and who follows them?** Especially: which accounts are in their "first 50 followers" — this often reveals the launching cluster.
- **Who do they amplify?** Reply chains, retweets, quote-tweets.
- **Who amplifies them?** Especially: do they receive coordinated bursts of amplification?
- **Cross-platform overlap** — does the same handle, or the same content, appear on multiple platforms with the same launch date?

Tools and methods:
- Platform-native search and follower lists
- **Bot Sentinel**, **Botometer** — bot likelihood scores (treat as one signal, not a verdict)
- For X/Twitter (where API access is restricted in 2026): scraping should be done within Terms of Service, and archived screenshots are usually more defensible than live data
- For TikTok / Instagram: Meta's CrowdTangle was discontinued; current alternatives include Junkipedia, Hoaxy (limited), and partnerships with academic projects

### 4. Behaviour — what is the account doing, and to what end?

- **Posting cadence** — what hours of day / days of week? An account that posts 8 hours a day, every day, including holidays, is unlikely to be a single hobbyist.
- **Posting tempo across the network** — many of the strongest "coordinated inauthentic behaviour" findings come from time-series analysis: when one account posts, do many others post very similar content within 60 seconds?
- **Topical focus** — does the account stick to a narrow set of topics that align with a known campaign?
- **Language register and translation tells** — non-native phrasing, machine-translation artefacts, repeated unusual word choices
- **Linkages to known operators** — does the content link to domains or accounts already documented as part of an influence operation?

## Output format

A social-account investigation lead sheet, on top of the standard sections, includes:

- **Account snapshot** — handle(s), display name(s), creation date, current follower / following / post count, profile photo, bio (with translation if needed)
- **Authenticity assessment** — Authentic / Likely authentic / Inauthentic indicators present / Likely inauthentic / Demonstrably inauthentic, with itemised evidence
- **Network map (text or visual)** — top 10 accounts followed, top 10 amplifiers, with notes on each
- **Behavioural pattern table** — posting hours, posting cadence, topical focus, with charts if useful
- **Coordination evidence (if applicable)** — other accounts behaving identically, with timestamps showing the pattern
- **Recommended platform action** (if appropriate) — should the journalist refer this to the platform's trust & safety team, or to a researcher?

## Special considerations

### Anonymous accounts that may be human-rights defenders

Many anonymous accounts are run by activists, dissidents, journalists in hostile environments, or whistleblowers — for whom anonymity is a safety necessity. **Doxing such accounts can endanger lives.** If your investigation is heading toward identifying an anonymous account that could plausibly belong to a vulnerable person, stop and consult the editor before continuing. The default is to not unmask.

### Platform Terms of Service

Most platforms forbid automated scraping at scale. Respect ToS. For journalistic investigations, manual review and screenshotting is usually defensible; large-scale scraping may not be. If the investigation requires scale, partner with an academic research group that has data-use agreements.

### Archiving social-media content

Social-media content is *especially* ephemeral. Archive every relevant post via:
- Native platform "save link" + screenshot
- archive.today (works on most platforms even when archive.org is blocked)
- archive.org (Wayback Machine) — submit explicitly, since social-media URLs are not auto-crawled
- For deleted-post recovery: archive.org may have a snapshot; Politwoops captures politicians' deleted tweets

## References

- DFRLab (Atlantic Council Digital Forensic Research Lab): https://dfrlab.org/
- Stanford Internet Observatory archive of past investigations: https://cyber.fsi.stanford.edu/io
- The OSoMe lab at Indiana (Hoaxy, Botometer history): https://osome.iu.edu/
- For coordinated-campaign methodology: see the `social-media-intelligence` skill in this workspace
