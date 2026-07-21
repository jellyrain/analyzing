import { Moon, Sun } from "lucide-react"

import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"

/** 亮暗主题切换，首次连接页和完整工作区共用。 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === "dark"

  return (
    <Button
      aria-label={isDark ? "切换到亮色模式" : "切换到暗色模式"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      size="icon"
      title={isDark ? "切换到亮色模式" : "切换到暗色模式"}
      variant="ghost"
    >
      {isDark ? <Sun /> : <Moon />}
    </Button>
  )
}
