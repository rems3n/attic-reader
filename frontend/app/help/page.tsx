import Link from "next/link";
import PageHeader from "../../components/PageHeader";
export default function Help() {
  return (
    <main className="shell narrowShell">
      <PageHeader title="Help" eyebrow="ATTIC READER">
        Learn how lessons, reading, and practice fit together.
      </PageHeader>
      <section className="card anchorTarget" id="overview">
        <h2>Choose a starting point</h2>
        <p>
          New to Greek? <Link href="/start">Start with the alphabet</Link>. If
          you have studied before, use the{" "}
          <Link href="/learn/placement">placement test</Link>. You can also open
          the <Link href="/library">Library</Link> to read and listen directly.
        </p>
      </section>
      <section className="card anchorTarget" id="lessons">
        <h2>Work through a lesson</h2>
        <p>
          Each lesson takes you through its goals, new words, a story,
          listening, comprehension, grammar, exercises, and a final check. Use
          the step buttons to move between sections. Some lessons also include
          composition and cultural context.
        </p>
        <p>
          Score at least 80% on the lesson check to complete it. You can revisit
          finished lessons. Unit tests open 24 hours after you finish a unit,
          giving you a chance to check what you remember.
        </p>
        <Link href="/learn">Open Learn →</Link>
      </section>
      <section className="card anchorTarget" id="practice">
        <h2>Review words and grammar</h2>
        <p>
          Words lets you choose a deck and practise Greek-to-English,
          English-to-Greek, forms, or principal parts. Reveal each answer, then
          choose Again, Hard, Good, or Easy. Those ratings determine when a card
          is due again.
        </p>
        <p>
          Practice offers weak-skill drills and a mistakes review. Mistakes
          leave the review deck after two correct answers in a row. The Home
          counter counts a word as known when a card has a review
          interval of at least 21 days.
        </p>
        <Link href="/practice">Open Practice →</Link>
      </section>
      <section className="card anchorTarget" id="reading">
        <h2>Read and listen</h2>
        <p>
          Choose a passage in the Library, or{" "}
          <Link href="/library/new">add a text</Link> by pasting Greek or
          photographing a page. Check OCR results before listening. Play a
          sentence or the whole passage, adjust the speed, and repeat as needed.
        </p>
        <p>
          The word-coverage panel links unfamiliar vocabulary to a study deck.
          Word pages show meanings, forms, and examples.
        </p>
      </section>
      <section className="card" id="pronunciation">
        <h2>Pronunciation</h2>
        <p>
          The audio uses reconstructed Classical Attic pronunciation, with a
          learner-friendly accent cue. It is designed for Classical Greek texts,
          rather than Modern Greek. A synthetic voice is a reading aid; not
          every story clip has received a human pronunciation review.
        </p>
      </section>
      <section className="card" id="data">
        <h2>Progress and offline use</h2>
        <p>
          Guest progress is saved in this browser. Clearing browser data or
          switching devices does not preserve it automatically.{" "}
          <Link href="/settings">Export a backup in Settings</Link>, or use a
          sync code.
        </p>
        <p>
          Pages and audio you have already opened can be available offline. Open
          a lesson and play its audio while connected before relying on it
          offline. OCR and uncached audio need a connection.
        </p>
      </section>
    </main>
  );
}
