export function ReadOnlyBanner() {
  return (
    <p className="rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-300">
      You're viewing <strong>main</strong> — read-only. Create or switch to a
      forecast branch (top right) to make changes.
    </p>
  );
}
