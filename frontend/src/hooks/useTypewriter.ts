import { useState, useEffect, useRef } from 'react'

export function useTypewriter(text: string, speed: number = 30) {
    // IMMEDIATE RETURN: Removed typewriter effect for instant display
    return { displayedText: text, isComplete: true }
}
