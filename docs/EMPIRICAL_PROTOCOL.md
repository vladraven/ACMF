# Empirical Protocol

A minimal hypothesis-ladder CSV requires:

```text
t, dy, x
```

Optional columns:

```text
z       expanded-state candidate for H2
stress  regime feature for H1
regime  explicit regime labels
```

The empirical runner does not fabricate missing variables. If `z` is absent, H2 cannot be tested. If `stress` or `regime` is absent, H1 cannot be tested.

Recommended full ACMF validation requires panel data with:

- population and age cohorts;
- fertility;
- migration;
- productivity;
- automation proxies;
- institutional proxies;
- stress proxies;
- latent-state candidates such as trust or institutional memory.
