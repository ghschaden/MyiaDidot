# Using Myia Didot with LuaLaTeX

Everything here was tested with LuaLaTeX (TeX Live 2026), `fontspec`,
and `babel` or `polyglossia`, with the OpenType (`.otf`) fonts. XeLaTeX
works the same way for the font setup; the language parts below are
written for LuaLaTeX.

## Loading the font

If the fonts are installed on your system (see [README](../README.md)),
load them by name:

```latex
\usepackage{fontspec}
\setmainfont{Myia Didot}
```

fontspec finds the four styles itself, so `\textit`, `\textbf` and
`\textbf{\textit{…}}` work at once.

Without installing them, point fontspec at the files, for example in a
`fonts/` folder next to your document:

```latex
\usepackage{fontspec}
\setmainfont{MyiaDidot}[
  Path           = ./fonts/,
  Extension      = .otf,
  UprightFont    = *-Regular,
  ItalicFont     = *-Italic,
  BoldFont       = *-Bold,
  BoldItalicFont = *-BoldItalic,
]
```

Options for the whole document go into the same brackets, for example
`Numbers = OldStyle` for old-style figures throughout.

## Several languages: babel

For Greek, Cyrillic or other languages with their own forms, let babel
load the languages from its `.ini` files (`provide*=*`) and give the font
with `\babelfont` instead of `\setmainfont`. Babel then tells the font
which language each passage is in, which switches on its localized forms
(Bulgarian and Serbian letters, Romanian ș ț, Dutch ÍJ, Catalan ŀl):

```latex
\usepackage{fontspec}
\usepackage[polytonicgreek, russian, bulgarian, serbian-cyrillic,
            english, provide*=*]{babel}
\babelfont{rm}[
  Path           = ./fonts/,
  Extension      = .otf,
  UprightFont    = *-Regular,
  ItalicFont     = *-Italic,
  BoldFont       = *-Bold,
  BoldItalicFont = *-BoldItalic,
]{MyiaDidot}
% installed fonts: \babelfont{rm}{Myia Didot}
```

The last language in the list is the main one. Switch with
`\foreignlanguage{bulgarian}{…}` or the `otherlanguage` environment:

```latex
\foreignlanguage{polytonicgreek}{Ἐν ἀρχῇ ἦν ὁ λόγος}
\foreignlanguage{bulgarian}{\textit{вдигнете ръце}}   % Bulgarian forms
\foreignlanguage{serbian-cyrillic}{\textit{бгдпт}}    % Serbian italic forms
```

Load the languages this way, not with babel's older options alone
(`\usepackage[bulgarian,russian]{babel}`): with those, Bulgarian next to
Russian fails to compile, and the font is not told the language.

## Several languages: polyglossia

polyglossia works as well; use it or babel, not both. Set the font with
`\setmainfont` as above; polyglossia tells it each passage's language
itself, so the same localized forms appear:

```latex
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{english}
\setotherlanguage[variant=polytonic]{greek}
\setotherlanguages{russian, bulgarian, dutch, catalan, romanian}
\setotherlanguage[script=cyrillic]{serbian}
\setmainfont{Myia Didot}   % or with Path = ... as above
```

Each language then has its command and environment:

```latex
\textgreek{Ἐν ἀρχῇ ἦν ὁ λόγος}
\textbulgarian{\textit{вдигнете ръце}}   % Bulgarian forms
\textserbian{\textit{бгдпт}}             % Serbian forms
\begin{catalan} col·legi \end{catalan}  % ŀl
```

Serbian's option is `script=cyrillic`, in lowercase (Cyrillic is also its
default); `script=Cyrillic` is not recognized. polyglossia shapes the
text with HarfBuzz, so copying text out of the PDF gives what you typed
(`l·l`, `ÍJ`), not the forms drawn.

## Features

All features can be set for the whole font (in the brackets of
`\setmainfont` or `\babelfont`) or for a passage with
`{\addfontfeatures{…} text}`.

| What | fontspec | Feature |
|---|---|---|
| Small capitals | `\textsc{Text}` | `smcp` |
| Capitals as small caps | `Letters = UppercaseSmallCaps` | `c2sc` |
| Old-style / lining figures | `Numbers = OldStyle` / `Numbers = Lining` | `onum` / `lnum` |
| Tabular / proportional figures | `Numbers = Monospaced` / `Numbers = Proportional` | `tnum` / `pnum` |
| Slashed zero | `Numbers = SlashedZero` | `zero` |
| Fractions (1/2 → ½) | `Fractions = On` | `frac` |
| Superior / inferior figures | `VerticalPosition = Superior` / `= Inferior` | `sups` / `sinf` |
| Discretionary ligatures ct st sp Qu Th th tt | `Ligatures = Rare` | `dlig` |
| Long s (ſ, with its ligatures ſt ſſ …) | `Style = Historic` | `hist` |
| Romanian ș ț without the language | `StylisticSet = 1` | `ss01` |
| SS for ß in small caps | `StylisticSet = 2` | `ss02` |
| Greek initial and medial theta | `StylisticSet = 11` | `ss11` |

The standard ligatures (fi ff fl …), kerning and the case-sensitive forms
are on by default. Note that long s is `Style = Historic`, not
`Ligatures = Historic` (that is `hlig`, which this font does not use).
Long s is set by a simple rule (s before a letter); German texts that
need it placed by word parts are better typed with ſ directly.

Greek small capitals drop their accents and breathings, as Greek
typography wants: `\textsc{Λόγος}` gives ΛΟΓΟΣ in small caps.

## Ligatures

**Standard ligatures** are on without asking: fi fl ff ffi ffl, and for
words like *Aufbau, Hofhund, Kafka, Schaft* also fb fh fj fk ft and ffb
ffh ffj ffk fft.

**Long-s ligatures** (ſt ſſ ſi ſl ſh ſk ſb ſſi ſſl) appear wherever the
text has a long s: type ſ (U+017F) yourself, or let the font put it in
with `Style = Historic` (*Wiſſenſchaft, Unſinn*). They are part of the
standard ligatures, so nothing else is needed.

**The decorative ligatures** are discretionary: ct, st and sp, with a
curl joining the two letters; Qu, the Q's tail drawn out of its bowl and
under the u as a swash; Th, the T's crossbar running on to the h; and
th, joined by the t's crossbar in the upright styles and by an arch from
the t's top to the h's in the italics; and tt, two t's on one crossbar. Switch them on with
`Ligatures = Rare`, for a passage or the whole document:

```latex
{\addfontfeatures{Ligatures=Rare} The strict act of the other}   % passage
\setmainfont{Myia Didot}[Ligatures = Rare]          % everywhere
```

To switch the standard ligatures off, use `Ligatures = NoCommon`; it can
be combined with the decorative ones, `Ligatures = {Rare, NoCommon}`.
To break a single ligature, put `\/` or `\kern0pt` between the letters
(`Auf\/lage`); in German with babel, the shorthand `"|` does the same
(`Auf"|lage`).

## A complete example

```latex
\documentclass{article}
\usepackage{fontspec}
\usepackage[polytonicgreek, russian, english, provide*=*]{babel}
\babelfont{rm}[Numbers = OldStyle]{Myia Didot}

\begin{document}
\section{On Myia}
A \textbf{letter} to Phyllis \textit{(on the care of a newborn)} has
come down under Myia's name, beginning
\foreignlanguage{polytonicgreek}{Μυῖα Φυλλίδι χαίρειν}; it is printed
in \textsc{Thesleff}'s edition of 1965.
\end{document}
```

Compile with `lualatex document.tex`.
