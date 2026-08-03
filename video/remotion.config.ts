/**
 * 高质量发布片渲染配置。
 *
 * PNG 中间帧避免 JPEG 对文字、细线和浅色渐变造成压缩噪点。
 * 最终编码质量仍可通过 render 命令的 --crf 参数控制。
 */
import {Config} from "@remotion/cli/config";

Config.setVideoImageFormat("png");
Config.setOverwriteOutput(true);
