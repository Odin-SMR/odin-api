<?php

final class ArcanistEslintLinter extends ArcanistExternalLinter {
  private $execution;

  public function getLinterName() {
    return 'Eslint';
  }

  public function getInfoURI() {
    return 'http://eslint.org/';
  }

  public function getInfoDescription() {
    return pht('The pluggable linting utility for JavaScript and JSX');
  }

  public function getInstallInstructions() {
      return 'Run npm install in the root of the repository';
  }

  public function getLinterConfigurationName() {
    return 'eslint';
  }

  public function getDefaultBinary() {
      return $this->getProjectRoot() . '/node_modules/.bin/eslint';
  }

  protected function getMandatoryFlags() {
    return array('--format=json', '--no-color');
  }

  protected function parseLinterOutput($path, $err, $stdout, $stderr) {
    $json = json_decode($stdout, true);

    $severity = ArcanistLintSeverity::SEVERITY_WARNING;

    $messages = array();

    foreach ($json as $file) {
      foreach ($file['messages'] as $offense) {
        $message = new ArcanistLintMessage();
        $message->setPath($file['filePath']);
        $message->setLine($offense['line']);
        $message->setChar($offense['column']);
        $message->setCode(isset($offense['ruleId']) ? $offense['ruleId'] : 'Parsing error');
        $message->setName($this->getInfoName());
        $message->setDescription($offense['message']);
        $message->setseverity($severity);

        $messages[] = $message;
      }
    }

    return $messages;
  }

}
