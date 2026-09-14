/** `text` with the first occurrence of `form` wrapped in <mark>. */
export default function Highlight({ text, form }: { text: string; form: string }) {
  const i = form ? text.indexOf(form) : -1;
  if (i < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, i)}
      <mark>{form}</mark>
      {text.slice(i + form.length)}
    </>
  );
}
