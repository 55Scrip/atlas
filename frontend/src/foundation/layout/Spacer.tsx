/**
 * Flexible spacer for use inside Stack/Inline — grows to fill available
 * space, pushing surrounding content apart. Deliberately not a
 * fixed-size gap element: no non-zero spacing token exists anywhere in
 * the corpus (see tokenRefs.ts), so a fixed size would have to be
 * invented. `flex: 1` is flex layout mechanics, not a design value.
 */
export function Spacer() {
  return <div aria-hidden="true" style={{ flex: 1 }} />;
}
