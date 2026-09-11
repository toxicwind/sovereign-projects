<script lang="ts">
  import { onMount } from "svelte";
  import { Play, RotateCw, CheckCircle2, XCircle, Clock, Zap, DollarSign, Database } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardHeader, CardTitle, CardContent } from "$lib/components/ui/card/index.js";
  import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "$lib/components/ui/table/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";

  interface BenchResult {
    model: string;
    provider: string;
    ok: boolean;
    ttftMs: number;
    tps: number;
    cost: number;
    error?: string;
  }

  let running = $state(false);
  let results = $state<BenchResult[]>([]);
  let error = $state<string | null>(null);

  async function loadCached() {
    try {
      const res = await fetch("/api/benchmarks/results");
      if (res.ok) {
        results = await res.json();
      }
    } catch (e: any) {
      // Fallback demo/initial data
    }
  }

  async function startBenchmark() {
    running = true;
    error = null;
    try {
      const res = await fetch("/api/benchmarks/run", { method: "POST" });
      if (!res.ok) throw new Error(`Benchmark run failed: ${res.statusText}`);
      const data = await res.json();
      results = data.results || [];
    } catch (e: any) {
      error = e.message;
    } finally {
      running = false;
    }
  }

  onMount(() => {
    loadCached();
  });
</script>

<div class="flex flex-col gap-6 p-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Benchmark Suite</h1>
      <p class="text-sm text-muted-foreground">
        Live empirical latency, throughput (TPS), and correctness telemetry across local RTX 3090 and cloud providers.
      </p>
    </div>
    <div class="flex items-center gap-3">
      <Button variant="outline" size="sm" onclick={loadCached} disabled={running}>
        <RotateCw class="mr-2 h-4 w-4 {running ? 'animate-spin' : ''}" />
        Refresh
      </Button>
      <Button size="sm" onclick={startBenchmark} disabled={running} class="bg-primary text-primary-foreground">
        <Play class="mr-2 h-4 w-4" />
        {running ? "Benchmarking..." : "Run Benchmark Sweep"}
      </Button>
    </div>
  </div>

  {#if error}
    <div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
      {error}
    </div>
  {/if}

  <div class="grid gap-4 md:grid-cols-4">
    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-2">
        <CardTitle class="text-sm font-medium">Total Tested</CardTitle>
        <Database class="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{results.length}</div>
        <p class="text-xs text-muted-foreground">Models tracked in DB</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-2">
        <CardTitle class="text-sm font-medium">Pass Rate</CardTitle>
        <CheckCircle2 class="h-4 w-4 text-success" />
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">
          {results.length ? Math.round((results.filter((r) => r.ok).length / results.length) * 100) : 0}%
        </div>
        <p class="text-xs text-muted-foreground">Syntactically correct</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-2">
        <CardTitle class="text-sm font-medium">Fastest TTFT</CardTitle>
        <Clock class="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">
          {results.filter((r) => r.ok).length ? Math.min(...results.filter((r) => r.ok).map((r) => r.ttftMs)) : 0}ms
        </div>
        <p class="text-xs text-muted-foreground">Sub-second response</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-2">
        <CardTitle class="text-sm font-medium">Peak Throughput</CardTitle>
        <Zap class="h-4 w-4 text-warning" />
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">
          {results.filter((r) => r.ok).length ? Math.max(...results.filter((r) => r.ok).map((r) => r.tps)).toFixed(1) : 0} tok/s
        </div>
        <p class="text-xs text-muted-foreground">Generation speed</p>
      </CardContent>
    </Card>
  </div>

  <Card>
    <CardHeader>
      <CardTitle class="text-base">Empirical Telemetry Matrix</CardTitle>
    </CardHeader>
    <CardContent>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model / Selector</TableHead>
            <TableHead>Provider</TableHead>
            <TableHead>Status</TableHead>
            <TableHead class="text-right">TTFT (p50)</TableHead>
            <TableHead class="text-right">Throughput</TableHead>
            <TableHead class="text-right">Cost</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {#each results as r}
            <TableRow>
              <TableCell class="font-medium">{r.model}</TableCell>
              <TableCell>{r.provider}</TableCell>
              <TableCell>
                {#if r.ok}
                  <Badge variant="outline" class="border-success/30 bg-success/10 text-success">
                    PASS
                  </Badge>
                {:else}
                  <Badge variant="outline" class="border-destructive/30 bg-destructive/10 text-destructive">
                    FAIL
                  </Badge>
                {/if}
              </TableCell>
              <TableCell class="text-right">{r.ok ? `${r.ttftMs}ms` : "-"}</TableCell>
              <TableCell class="text-right">{r.ok ? `${r.tps.toFixed(1)} tps` : "-"}</TableCell>
              <TableCell class="text-right">{r.ok ? `$${r.cost.toFixed(4)}` : "-"}</TableCell>
            </TableRow>
          {/each}
        </TableBody>
      </Table>
    </CardContent>
  </Card>
</div>
