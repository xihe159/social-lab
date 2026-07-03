import { RefreshCw } from "lucide-react";
import type { FormData } from "@/lib/social-lab-types";

type PersonScreenProps = {
  form: FormData;
  onFormChange: (patch: Partial<FormData>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
};

export function PersonScreen({
  form,
  onFormChange,
  onGenerate,
  isGenerating,
}: PersonScreenProps) {
  return (
    <section className="screen is-current">
      <div className="screen-heading">
        <span>Step 2 / 5 - 人物</span>
        <h2>你想模拟谁？</h2>
      </div>

      <div className="form-stack two-column">
        <label>
          <span>身份</span>
          <input
            value={form.role}
            onChange={(event) => onFormChange({ role: event.target.value })}
          />
        </label>
        <label>
          <span>你们现在是什么关系？</span>
          <input
            value={form.relation}
            onChange={(event) => onFormChange({ relation: event.target.value })}
          />
        </label>
        <label>
          <span>他/她平时怎么沟通？</span>
          <textarea
            value={form.habit}
            onChange={(event) => onFormChange({ habit: event.target.value })}
          />
        </label>
        <label>
          <span>可选：粘贴聊天记录</span>
          <textarea
            value={form.chatLog}
            onChange={(event) => onFormChange({ chatLog: event.target.value })}
            placeholder="可以粘贴微信、邮件或短信片段。建议先删除姓名、电话等隐私信息。"
          />
        </label>
      </div>

      <div className="inline-warning">
        <strong>请先去除敏感信息</strong>
        <p>
          Social Lab
          不会自动联系真实人物，也不承诺完全还原对方。这里生成的是一次沟通模拟参数。
        </p>
      </div>

      <div className="footer-actions">
        <button
          className="primary-action"
          disabled={isGenerating}
          onClick={onGenerate}
          type="button"
        >
          {isGenerating ? "正在生成画像..." : "生成画像"}{" "}
          <RefreshCw size={18} />
        </button>
      </div>
    </section>
  );
}
