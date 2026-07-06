import { ArrowRight, LoaderCircle } from "lucide-react";
import type { FormData } from "@/lib/social-lab-types";

type PersonScreenProps = {
  form: FormData;
  onFormChange: (patch: Partial<FormData>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  canGenerate: boolean;
};

export function PersonScreen({
  form,
  onFormChange,
  onGenerate,
  isGenerating,
  canGenerate,
}: PersonScreenProps) {
  const buttonLabel = isGenerating
    ? "正在生成画像..."
    : canGenerate
      ? "生成沟通对象"
      : "请先完成必填信息";

  return (
    <section className="screen person-screen is-current">
      <div className="screen-heading">
        <span>第 2 步，共 5 步</span>
        <h2>人物信息</h2>
        <p>补充对方的信息，让模拟更像真实沟通对象。</p>
      </div>

      <div className="form-stack two-column">
        <label>
          <span>这个人是谁？</span>
          <input
            value={form.role}
            onChange={(event) => onFormChange({ role: event.target.value })}
            placeholder="例如：直属领导 / 同事 / HR"
          />
        </label>
        <label>
          <span>你们现在是什么关系？</span>
          <input
            value={form.relation}
            onChange={(event) => onFormChange({ relation: event.target.value })}
            placeholder="例如：合作顺畅，但平时联系不多"
          />
        </label>
        <label>
          <span>他/她平时怎么沟通？</span>
          <textarea
            value={form.habit}
            onChange={(event) => onFormChange({ habit: event.target.value })}
            placeholder="例如：回复慢，比较严谨，喜欢有逻辑和证据"
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
        <p>
          隐私提示：请先删除姓名、电话、地址等敏感信息。Social Lab
          只会生成一次模拟参数，不会联系真实人物。
        </p>
      </div>

      <div className="footer-actions">
        <button
          className="primary-action"
          disabled={!canGenerate || isGenerating}
          onClick={onGenerate}
          type="button"
        >
          {buttonLabel}{" "}
          {isGenerating ? (
            <LoaderCircle className="spin-icon" size={18} />
          ) : (
            <ArrowRight size={18} />
          )}
        </button>
      </div>
    </section>
  );
}
