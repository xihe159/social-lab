const DEFAULT_CLOUDBASE_ENV_ID = "social-lab-d4g9g9ab34e44d7cb";
const DEFAULT_CLOUDBASE_REGION = "ap-shanghai";
const DEFAULT_CLOUDBASE_PUBLISHABLE_KEY =
  "eyJhbGciOiJSUzI1NiIsImtpZCI6IjlkMWRjMzFlLWI0ZDAtNDQ4Yi1hNzZmLWIwY2M2M2Q4MTQ5OCJ9.eyJpc3MiOiJodHRwczovL3NvY2lhbC1sYWItZDRnOWc5YWIzNGU0NGQ3Y2IuYXAtc2hhbmdoYWkudGNiLWFwaS50ZW5jZW50Y2xvdWRhcGkuY29tIiwic3ViIjoiYW5vbiIsImF1ZCI6InNvY2lhbC1sYWItZDRnOWc5YWIzNGU0NGQ3Y2IiLCJleHAiOjQwODc0NTAzMjEsImlhdCI6MTc4Mzc2NzEyMSwibm9uY2UiOiItYXp3eUt1blJULUZIMEVxN0p3STNRIiwiYXRfaGFzaCI6Ii1hend5S3VuUlQtRkgwRXE3SndJM1EiLCJuYW1lIjoiQW5vbnltb3VzIiwic2NvcGUiOiJhbm9ueW1vdXMiLCJwcm9qZWN0X2lkIjoic29jaWFsLWxhYi1kNGc5ZzlhYjM0ZTQ0ZDdjYiIsIm1ldGEiOnsicGxhdGZvcm0iOiJQdWJsaXNoYWJsZUtleSJ9LCJ1c2VyX3R5cGUiOiIiLCJjbGllbnRfdHlwZSI6ImNsaWVudF91c2VyIiwiaXNfc3lzdGVtX2FkbWluIjpmYWxzZX0.qedLzQ2FZm0BZ-1Los7f4z20MlNnU2MHLLuvoPKpEroSe299CJHr-n4mdNQfu3rd0ze3byb3XiD_EG5nkGZHpaorQiFXcXyAtfaIMdSoMlZushTnTRVONTLVY9811QATwOrf41wgNXNmeiEQPAFl80qk3LLeOZFlk-jTIQNqj8Imd_EbtR61sgAWbCfl2gHTsJkPpFw6QcdtUeOK1K-haqPwamuBwEfQv7vKPS0ldTRYnWiSfjuHQDKonpzJJJpTGp5ZjrD5zGZCwdeQ2w-EHOmUmE6MixFx9086JDE5LrZPojqCTPUZVLEnS-lnZt5xWdRw2iSA1jX6L-ASQ_-UCg";

const cloudbaseEnvId =
  process.env.NEXT_PUBLIC_CLOUDBASE_ENV_ID || DEFAULT_CLOUDBASE_ENV_ID;
const cloudbaseRegion =
  process.env.NEXT_PUBLIC_CLOUDBASE_REGION || DEFAULT_CLOUDBASE_REGION;
const cloudbasePublishableKey =
  process.env.NEXT_PUBLIC_CLOUDBASE_PUBLISHABLE_KEY ||
  DEFAULT_CLOUDBASE_PUBLISHABLE_KEY;

export const isCloudBaseConfigured = Boolean(cloudbaseEnvId);

type CloudBaseApp = {
  auth: () => any;
  database: () => any;
};

let appPromise: Promise<CloudBaseApp | null> | null = null;

export async function getCloudBaseApp() {
  if (!isCloudBaseConfigured || typeof window === "undefined") return null;

  appPromise ??= import("@cloudbase/js-sdk").then((module) => {
    const cloudbase = module.default || module;
    return cloudbase.init({
      env: cloudbaseEnvId,
      region: cloudbaseRegion,
      accessKey: cloudbasePublishableKey,
    }) as CloudBaseApp;
  });

  return appPromise;
}

export async function getCloudBaseAuth() {
  const app = await getCloudBaseApp();
  return app?.auth() ?? null;
}

export async function getCloudBaseDb() {
  const app = await getCloudBaseApp();
  return app?.database() ?? null;
}
