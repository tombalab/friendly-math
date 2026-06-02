import {
  BarChart,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
} from "cursor/canvas";

type Status = "Dobre" | "Częściowe" | "Luka" | "Ryzyko";

const statusTone: Record<Status, "success" | "warning" | "neutral" | "info"> = {
  Dobre: "success",
  Częściowe: "warning",
  Luka: "neutral",
  Ryzyko: "info",
};

function StatusPill({ status }: { status: Status }) {
  return (
    <Pill tone={statusTone[status]} active={status !== "Luka"} size="sm">
      {status}
    </Pill>
  );
}

const earlyRows = [
  [
    "Liczby i własności liczb",
    "liczenie po, porównywanie liczb",
    "1–3",
    "Dobre",
    "Zgodne z PP: liczenie w przód/wstecz, porównywanie, kolejność. Dodać wzorce dla porównywania kl. 1 i 3.",
  ],
  [
    "Dodawanie i odejmowanie",
    "dodawanie/odejmowanie do 20, 100, 1000",
    "1–3",
    "Dobre",
    "Najmocniejszy obszar. W kl. 3 tematy do 20 są raczej powtórką, warto oznaczyć je jako uproszczone.",
  ],
  [
    "Mnożenie, dzielenie, okienko",
    "tabliczka mnożenia, mnożenie przez 10, dzielenie, równania z okienkiem",
    "2–3",
    "Dobre",
    "Zgodne z PP. Brakuje wzorców dla części tematów z kl. 2–3, ale generator ma blueprinty i klucz.",
  ],
  [
    "Czytanie tekstów matematycznych",
    "zadania tekstowe",
    "1–3",
    "Częściowe",
    "Temat istnieje, ale klucz odpowiedzi ma support none. Trzeba uczciwie oznaczać ręczną weryfikację.",
  ],
  [
    "Ułamki intuicyjne",
    "ułamki",
    "2–3",
    "Częściowe",
    "Połowa i ćwierć są częściowo wspierane. Zadania typu pokoloruj/podziel figurę wymagają recenzji nauczyciela.",
  ],
  [
    "Sytuacje praktyczne",
    "pieniądze, czas, pomiary długości, obwody",
    "1–3",
    "Ryzyko",
    "Opcje są w UI, ale answer_support none. PDF może wyglądać kompletnie mimo braku pełnego klucza.",
  ],
  [
    "Geometria i stosunki przestrzenne",
    "brak osobnych tematów poza obwodami",
    "1–3",
    "Luka",
    "PP wymaga figur, położenia, mierzenia, symetrii. W UI brakuje oddzielnych tematów i wzorców.",
  ],
  [
    "Masa, temperatura, pojemność, szacowanie",
    "brak",
    "1–3",
    "Luka",
    "Wymagania PP są obecne, ale nie ma tematów w katalogu ani generatorze.",
  ],
] as const;

const olderRows = [
  [
    "Liczby naturalne i działania",
    "dodawanie, odejmowanie, mnożenie, dzielenie",
    "4–8",
    "Częściowe",
    "UI ma ćwiczenia rachunkowe, ale blueprinty dla 5–8 korzystają z downgrade'u zamiast zakresów per klasa.",
  ],
  [
    "Liczby całkowite",
    "brak",
    "4–8",
    "Luka",
    "PP wymaga osi liczbowej, porównywania, wartości bezwzględnej i rachunków na liczbach całkowitych.",
  ],
  [
    "Ułamki zwykłe, dziesiętne, mieszane",
    "ułamki",
    "4–8",
    "Częściowe",
    "Obsługa skupia się na a/b o tym samym mianowniku. Brak dziesiętnych, mieszanych, skracania i rozszerzania.",
  ],
  [
    "Procenty i obliczenia praktyczne",
    "brak",
    "4–8",
    "Luka",
    "Brak kluczowego działu IV–VIII, szczególnie dla VII–VIII.",
  ],
  [
    "Algebra i równania",
    "równania",
    "4–8",
    "Ryzyko",
    "Blueprint i fallback używają x, a parser/wzorce preferują okienko. To rozjeżdża UI, PDF i klucz odpowiedzi.",
  ],
  [
    "Geometria płaska i przestrzenna",
    "brak",
    "4–8",
    "Luka",
    "Brak kątów, pól, brył, Pitagorasa, układu współrzędnych i zadań konstrukcyjnych.",
  ],
  [
    "Statystyka i dane",
    "brak",
    "4–8",
    "Luka",
    "PP wymaga tabel, diagramów i wykresów. Obecny PDF nie ma takich szablonów.",
  ],
  [
    "Potęgi, pierwiastki, proporcjonalność",
    "brak",
    "7–8",
    "Luka",
    "To zasadnicze treści VII–VIII; obecny produkt nie powinien deklarować pełnej zgodności dla tych klas.",
  ],
] as const;

const uiRisks = [
  ["Równania", "x w generatorze vs ☐ w parserze i wzorcach", "wysokie"],
  ["Odpowiedzi", "checkbox odpowiedzi przy tematach partial/none", "wysokie"],
  ["Klasy 4–8", "6 tematów ogólnych, downgrade blueprintów", "wysokie"],
  ["Klasa 3", "tematy do 20 jako normalna opcja zamiast powtórki", "średnie"],
  ["Wzorce", "22 JSON-y pomagają recenzji, ale nie są mapą PP", "średnie"],
] as const;

const phaseRows = [
  [
    "0. Uczciwość MVP",
    "1–2 dni",
    "Oznaczyć zakres 4–8 jako rachunkowy/beta, ujednolicić równania, dodać ostrzeżenia dla klucza partial/none.",
    "Mniejsze ryzyko wydruku karty, która wygląda pewnie, ale nie realizuje deklarowanego zakresu.",
  ],
  [
    "1. Macierz PP jako kontrakt",
    "1–2 dni",
    "Dodać dokument topic_id × klasa × wymaganie PP × status supportu. Użyć go jako źródła decyzji UI.",
    "Zespół wie, które tematy są zgodne, częściowe lub poza MVP.",
  ],
  [
    "2. Domknięcie klas 1–3",
    "3–5 dni",
    "Rozszerzyć wzorce i parser dla pieniędzy, czasu, jednostek, obwodów, zadań tekstowych; dodać geometrię prostą.",
    "Największy zwrot: klasy I–III mogą być realnie bliskie PP.",
  ],
  [
    "3. Stabilizacja klas 4–6",
    "4–7 dni",
    "Blueprinty per klasa dla działań, ułamków dziesiętnych, liczb całkowitych, procentów i pól/obwodów.",
    "UI 4–6 przestaje być tylko powtórką rachunkową.",
  ],
  [
    "4. Decyzja o 7–8",
    "2–3 dni planowania",
    "Wybrać: ukryć 7–8 do czasu pełnych tematów albo dodać zakres egzaminacyjny: potęgi, pierwiastki, algebra, procenty, Pitagoras.",
    "Produkt nie obiecuje więcej, niż potrafi bezpiecznie wygenerować.",
  ],
  [
    "5. Curriculum smoke tests",
    "2–4 dni",
    "Dla każdej opcji UI: blueprint, fallback, validator, answer status, PDF smoke, wzorzec lub jawna luka.",
    "Regresje w zgodności z PP są łapane automatycznie.",
  ],
] as const;

export default function CurriculumMatrixPlan() {
  const theme = useHostTheme();

  const earlyTableRows = earlyRows.map((row) => [
    row[0],
    row[1],
    row[2],
    <StatusPill status={row[3] as Status} />,
    row[4],
  ]);

  const olderTableRows = olderRows.map((row) => [
    row[0],
    row[1],
    row[2],
    <StatusPill status={row[3] as Status} />,
    row[4],
  ]);

  return (
    <Stack gap={18} style={{ padding: 24, maxWidth: 1280, margin: "0 auto" }}>
      <Stack gap={6}>
        <H1>Macierz zgodności z podstawą programową i plan fazowy</H1>
        <Text tone="secondary">
          Zakres: Friendly Math Streamlit MVP, dokumenty PP 2025/2026 dla edukacji wczesnoszkolnej oraz matematyki IV–VIII.
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="1–3" label="klasy blisko pokrycia rachunkowego" tone="success" />
        <Stat value="4–8" label="klasy wymagające zawężenia lub rozbudowy" tone="warning" />
        <Stat value="35" label="aktualne wzorce referencyjne" tone="info" />
        <Stat value="P0" label="najważniejsze: równania i odpowiedzi" tone="danger" />
      </Grid>

      <Grid columns="1.2fr 0.8fr" gap={16} align="start">
        <Stack gap={10}>
          <H2>Macierz: klasy 1–3</H2>
          <Table
            headers={["Obszar PP", "Opcje / tematy", "Klasy", "Status", "Wniosek"]}
            rows={earlyTableRows}
            rowTone={earlyRows.map((r) =>
              r[3] === "Dobre" ? "success" : r[3] === "Częściowe" ? "warning" : r[3] === "Ryzyko" ? "info" : "neutral"
            )}
            striped
            stickyHeader
          />
        </Stack>

        <Card>
          <CardHeader trailing={<Pill tone="success" active size="sm">silny rdzeń</Pill>}>
            Wniosek dla I–III
          </CardHeader>
          <CardBody>
            <Stack gap={10}>
              <Text>
                Rdzeń rachunkowy jest spójny z PP: liczby, porównywanie, działania, tabliczka, dzielenie i okienko mają sensowne blueprinty.
              </Text>
              <Text tone="secondary">
                Największa luka to matematyka praktyczna i geometria: tematy są częściowo w UI, ale klucz odpowiedzi i wzorce nie dają jeszcze pełnego zaufania.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Grid columns="1.2fr 0.8fr" gap={16} align="start">
        <Stack gap={10}>
          <H2>Macierz: klasy 4–8</H2>
          <Table
            headers={["Blok PP", "Opcje / tematy", "Klasy", "Status", "Wniosek"]}
            rows={olderTableRows}
            rowTone={olderRows.map((r) =>
              r[3] === "Dobre" ? "success" : r[3] === "Częściowe" ? "warning" : r[3] === "Ryzyko" ? "info" : "neutral"
            )}
            striped
            stickyHeader
          />
        </Stack>

        <Card>
          <CardHeader trailing={<Pill tone="warning" active size="sm">ograniczony zakres</Pill>}>
            Wniosek dla IV–VIII
          </CardHeader>
          <CardBody>
            <Stack gap={10}>
              <Text>
                Obecne klasy 4–8 należy traktować jako ćwiczenia rachunkowe, nie pełny generator zgodny z PP.
              </Text>
              <Text tone="secondary">
                Najpilniejsze jest rozdzielenie realnego zakresu MVP od długiej listy wymagań PP: liczby całkowite, procenty, geometria, statystyka, potęgi i pierwiastki są dziś poza produktem.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Grid columns="0.8fr 1.2fr" gap={16} align="start">
        <Card>
          <CardHeader>Pokrycie tematów UI według klasy</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small" tone="secondary">
                Liczba opcji widocznych w UI; nie oznacza pełnej zgodności z PP.
              </Text>
              <BarChart
                categories={["1", "2", "3", "4", "5", "6", "7", "8"]}
                series={[{ name: "Tematy UI", data: [8, 16, 18, 6, 6, 6, 6, 6], tone: "info" }]}
                height={240}
              />
              <Text size="small" tone="tertiary">
                Źródło: topic_labels_for_grade; stan po 22 wzorcach referencyjnych.
              </Text>
            </Stack>
          </CardBody>
        </Card>

        <Stack gap={10}>
          <H2>Ryzyka spójności UI → generator → PDF</H2>
          <Table
            headers={["Obszar", "Problem", "Priorytet"]}
            rows={uiRisks.map((r) => [
              r[0],
              r[1],
              <Pill tone={r[2] === "wysokie" ? "warning" : "info"} active={r[2] === "wysokie"} size="sm">
                {r[2]}
              </Pill>,
            ])}
            rowTone={uiRisks.map((r) => (r[2] === "wysokie" ? "warning" : "info"))}
            striped
          />
        </Stack>
      </Grid>

      <Divider />

      <Stack gap={10}>
        <H2>Plan fazowy</H2>
        <Table
          headers={["Faza", "Szacunek", "Zakres", "Efekt"]}
          rows={phaseRows.map((r) => [r[0], r[1], r[2], r[3]])}
          rowTone={["warning", "info", "success", "warning", "info", "success"]}
          striped
          stickyHeader
        />
      </Stack>

      <Grid columns={3} gap={14}>
        <Card>
          <CardHeader>Najpierw</CardHeader>
          <CardBody>
            <Text>
              Ujednolicić równania i komunikaty o częściowym kluczu odpowiedzi. To bezpośrednio wpływa na zaufanie do PDF.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Potem</CardHeader>
          <CardBody>
            <Text>
              Domknąć klasy 1–3, bo są najbliżej pełnej zgodności z PP i mają największy potencjał użytkowy w MVP.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Decyzja produktowa</CardHeader>
          <CardBody>
            <Text>
              Dla 7–8 wybrać: świadomie ograniczyć UI albo rozbudować katalog o działy egzaminacyjne.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Text size="small" tone="tertiary" style={{ borderTop: `1px solid ${theme.stroke.tertiary}`, paddingTop: 12 }}>
        Źródła: docs/podstawa-programowa-edukacja-wczesnoszkolna-matematyka-2025-2026.md, docs/podstawa-programowa-matematyka-sp-iv-viii-2025-2026.md, app/domain/topic_catalog.py, app/ai/topic_blueprints.py.
      </Text>
    </Stack>
  );
}
