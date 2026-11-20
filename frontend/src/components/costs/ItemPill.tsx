const base = "rounded-full px-2 py-0.5 text-xs font-medium";
const actualClasses = `${base} bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300`;
const estimateClasses = `${base} bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300`;

export function ItemPill({
  isActual,
  canEdit,
  label,
  onClick,
}: {
  isActual: boolean;
  canEdit: boolean;
  label: string;
  onClick: () => void;
}) {
  const text = isActual ? "A" : "Est";
  const classes = isActual ? actualClasses : estimateClasses;

  if (!canEdit) {
    return (
      <span
        className={classes}
        title={
          isActual
            ? "Actual cost recorded"
            : "Estimate — switch to a forecast branch to record the actual"
        }
      >
        {text}
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={isActual ? "Edit or remove this actual" : "Record the actual cost"}
      className={`${classes} cursor-pointer underline decoration-dotted underline-offset-2 hover:brightness-95 dark:hover:brightness-125`}
    >
      {text}
    </button>
  );
}
