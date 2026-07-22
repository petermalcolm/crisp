import { NavLink, Outlet } from "react-router-dom";
import { BranchSwitcher } from "../branch/BranchSwitcher";
import { ThemeToggle } from "./ThemeToggle";

const navItems = [
  { to: "/components", label: "Components" },
  { to: "/costs", label: "Costs" },
  { to: "/parameters", label: "Income/Expenses" },
  { to: "/ffb", label: "Fully Funded Balance" },
];

const linkClasses = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium ${
    isActive
      ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
  }`;

export function AppShell() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="text-lg font-semibold tracking-tight">
              CRISP
            </span>
            <nav className="flex flex-wrap gap-1">
              {navItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={linkClasses}>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <BranchSwitcher />
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
