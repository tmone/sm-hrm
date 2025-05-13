'use client';

import { useEffect, useLayoutEffect } from "react"

// Use this hook to fix the React useLayoutEffect warning during SSR
const useIsomorphicLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

export default useIsomorphicLayoutEffect;