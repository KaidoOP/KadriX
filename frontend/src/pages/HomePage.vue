<template>
  <q-page class="home-page">
    <section class="home-page__content">
      <div class="home-page__intro">
        <p class="home-page__eyebrow">IBM Bob Dev Day Hackathon</p>
        <h1>KadriX campaign workspace</h1>
        <p>
          A Quasar frontend shell for the campaign assistant. The backend can stay behind the
          API Gateway at <code>http://localhost:8000</code>.
        </p>
      </div>

      <q-card flat bordered class="home-page__panel">
        <q-card-section>
          <div class="text-subtitle1 text-weight-medium">Frontend setup</div>
          <div class="text-body2 text-grey-7">
            Vue 3, Vite, TypeScript, Quasar, and Axios are ready for the next UI step.
          </div>
        </q-card-section>
      </q-card>
    </section>
  </q-page>
</template>

<style scoped lang="scss">
.home-page {
  min-height: calc(100vh - 50px);
  background: #f6f8fa;
}

.home-page__content {
  width: min(960px, calc(100% - 32px));
  margin: 0 auto;
  padding: 56px 0;
}

.home-page__intro {
  max-width: 720px;

  h1 {
    margin: 0 0 16px;
    color: #172033;
    font-size: 40px;
    line-height: 1.1;
    font-weight: 700;
  }

  p {
    margin: 0;
    color: #4b5563;
    font-size: 16px;
    line-height: 1.6;
  }
}

.home-page__eyebrow {
  margin-bottom: 12px !important;
  color: #1f8a70 !important;
  font-size: 13px !important;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.home-page__panel {
  max-width: 520px;
  margin-top: 32px;
  border-radius: 8px;
}

@media (max-width: 640px) {
  .home-page__content {
    width: min(100% - 24px, 960px);
    padding: 36px 0;
  }

  .home-page__intro h1 {
    font-size: 32px;
  }
}
</style>
