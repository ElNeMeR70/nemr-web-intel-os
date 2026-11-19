"""
Nemr Web Intel OS - Tech Stack Fingerprinter & Contact Intelligence Miner (v3.0.0)
Extracts verified emails, phones, and social profiles while fingerprinting CMS/frameworks/CDNs/gateways.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


class TechContactMiner:
    """Extracts contact intelligence and fingerprints web application tech stacks."""

    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,10}\b")
    IMAGE_OR_ASSET_TLDS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".woff", ".woff2", ".css", ".js")
    PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{4}\b")

    SOCIAL_PATTERNS = {
        "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9_\-]+/?", re.IGNORECASE),
        "github": re.compile(r"https?://(?:www\.)?github\.com/[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_.\-]+)?", re.IGNORECASE),
        "x": re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+", re.IGNORECASE),
        "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.\-]+", re.IGNORECASE),
        "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+", re.IGNORECASE),
        "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/)[a-zA-Z0-9_\-]+", re.IGNORECASE),
        "whatsapp": re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com/send\?phone=)[0-9+&=]+", re.IGNORECASE),
    }

    HTML_SIGNATURES = {
        "WordPress": ("wp-content/", "wp-includes/", "wp-json"),
        "Shopify": ("cdn.shopify.com", "shopify.theme"),
        "Next.js": ("__next_data__", "/_next/static/"),
        "React": ("data-reactroot", "react-dom"),
        "Vue": ("data-v-", "__vue__"),
        "Laravel": ("laravel_session", "csrf-token"),
        "PHP": (".php", "x-powered-by: php"),
        "Stripe": ("js.stripe.com", "stripe-signature"),
        "Paymob": ("accept.paymob.com", "paymobsolutions"),
        "Google Tag Manager": ("googletagmanager.com/gtm.js",),
        "Tailwind CSS": ("tailwindcss", "dark:bg-slate-"),
    }

    @classmethod
    def analyze(cls, html: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        # 1. Emails (filtering fake filename retina assets like hero@2x.png)
        emails: List[str] = []
        for match in cls.EMAIL_RE.finditer(html):
            em = match.group(0).lower()
            if em.endswith(cls.IMAGE_OR_ASSET_TLDS):
                continue
            if em not in emails:
                emails.append(em)

        # 2. Phone numbers (require + prefix or 10+ digits cleanly)
        phones: List[str] = []
        for match in cls.PHONE_RE.finditer(html):
            raw_p = match.group(0).strip()
            digits = re.sub(r"\D", "", raw_p)
            if (raw_p.startswith("+") or len(digits) >= 10) and len(digits) <= 15:
                if raw_p not in phones:
                    phones.append(raw_p)

        # 3. Social Links
        socials: Dict[str, List[str]] = {}
        for platform, pat in cls.SOCIAL_PATTERNS.items():
            found = sorted(set(m.group(0) for m in pat.finditer(html)))
            if found:
                socials[platform] = found

        # 4. Tech Stack Fingerprinting (HTML + HTTP Headers)
        html_lower = html.lower()
        header_str = " ".join(f"{k.lower()}: {str(v).lower()}" for k, v in (headers or {}).items())
        tech_stack: List[str] = []

        for tech, markers in cls.HTML_SIGNATURES.items():
            if any(m in html_lower or m in header_str for m in markers):
                tech_stack.append(tech)

        hdr_lower = {k.lower(): str(v).lower() for k, v in (headers or {}).items()}
        server_val = hdr_lower.get("server", "")
        powered_val = hdr_lower.get("x-powered-by", "")
        if "cloudflare" in server_val or "cf-ray" in hdr_lower:
            tech_stack.append("Cloudflare")
        if "litespeed" in server_val:
            tech_stack.append("LiteSpeed")
        if "nginx" in server_val:
            tech_stack.append("Nginx")
        if "php" in powered_val and "PHP" not in tech_stack:
            tech_stack.append("PHP")

        return {
            "emails": emails,
            "phones": phones,
            "socials": socials,
            "tech_stack": sorted(set(tech_stack)),
        }
