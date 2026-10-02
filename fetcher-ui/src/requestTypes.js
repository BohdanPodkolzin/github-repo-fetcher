// Must match the keys of ENDPOINTS in fetcher-api/app/github.py.
export const REQUEST_TYPES = [
  { value: "repo", label: "Repo info" },
  { value: "commits", label: "Recent commits" },
  { value: "issues", label: "Open issues" },
  { value: "releases", label: "Releases" },
  { value: "contributors", label: "Contributors" },
  { value: "languages", label: "Languages" },
  { value: "user", label: "User profile" },
];

export function typeLabel(value) {
  return REQUEST_TYPES.find((t) => t.value === value)?.label ?? value;
}
