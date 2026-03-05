import type { ButtonHTMLAttributes } from 'react'

type PrimaryButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

export function PrimaryButton({ className, ...props }: PrimaryButtonProps) {
  const mergedClassName = className ? `button ${className}` : 'button'
  return <button className={mergedClassName} {...props} />
}
