/// Comunidade e fórum da Semente (Wallace Ross) — gerado em 23/11/2026 a partir de Semente.exe --servidor.
/// O PocketBase aplica este arquivo sozinho, uma vez, ao ligar (pasta pb_migrations).
migrate((db) => {
  const dao = new Dao(db);
  const snapshot = [
 {
  "id": "_pb_users_auth_",
  "name": "users",
  "type": "auth",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "users_name",
    "name": "name",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": null,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "users_avatar",
    "name": "avatar",
    "type": "file",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "mimeTypes": [
      "image/jpeg",
      "image/png",
      "image/svg+xml",
      "image/gif",
      "image/webp"
     ],
     "thumbs": null,
     "maxSelect": 1,
     "maxSize": 5242880,
     "protected": false
    }
   },
   {
    "system": false,
    "id": "ngzpgzgb",
    "name": "sobre",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 600,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "20slpie2",
    "name": "local",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 40,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "cbknwfer",
    "name": "aprovado",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   },
   {
    "system": false,
    "id": "jrfs8a5f",
    "name": "banido",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   },
   {
    "system": false,
    "id": "osvtmlll",
    "name": "banido_motivo",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 300,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "0hgyiy64",
    "name": "autor",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   }
  ],
  "indexes": [],
  "listRule": "",
  "viewRule": "",
  "createRule": "@request.data.autor:isset = false && @request.data.aprovado:isset = false && @request.data.banido:isset = false && @request.data.banido_motivo:isset = false",
  "updateRule": "(@request.auth.id = id && @request.data.autor:isset = false && @request.data.aprovado:isset = false && @request.data.banido:isset = false && @request.data.banido_motivo:isset = false) || @request.auth.autor = true",
  "deleteRule": null,
  "options": {
   "allowEmailAuth": true,
   "allowOAuth2Auth": true,
   "allowUsernameAuth": true,
   "exceptEmailDomains": null,
   "manageRule": null,
   "minPasswordLength": 8,
   "onlyEmailDomains": null,
   "onlyVerified": false,
   "requireEmail": false
  }
 },
 {
  "id": "3968ayh8jbvsqxx",
  "name": "canais",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "ytafef6k",
    "name": "nome",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 40,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "pgvo1h2v",
    "name": "descricao",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 200,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "hlqbe3jw",
    "name": "ordem",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": null,
     "noDecimal": true
    }
   },
   {
    "system": false,
    "id": "awmlncur",
    "name": "so_autor",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   }
  ],
  "indexes": [],
  "listRule": "",
  "viewRule": "",
  "createRule": "@request.auth.autor = true",
  "updateRule": "@request.auth.autor = true",
  "deleteRule": "@request.auth.autor = true",
  "options": {}
 },
 {
  "id": "1tj1gw00x8rptke",
  "name": "config",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "muvexrg9",
    "name": "regras_texto",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 4000,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "zrayfacg",
    "name": "aviso",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 300,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "0nsfco4a",
    "name": "so_aprovados",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   },
   {
    "system": false,
    "id": "690i6i9d",
    "name": "qarchis_de_membros",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   },
   {
    "system": false,
    "id": "6qm21tip",
    "name": "categorias",
    "type": "json",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "maxSize": 200000
    }
   }
  ],
  "indexes": [],
  "listRule": "",
  "viewRule": "",
  "createRule": null,
  "updateRule": "@request.auth.autor = true",
  "deleteRule": null,
  "options": {}
 },
 {
  "id": "2zdu7tifp5cfv4n",
  "name": "curtidas",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "eifnot8o",
    "name": "alvo",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 64,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "x1xrro2c",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   }
  ],
  "indexes": [
   "CREATE UNIQUE INDEX `idx_curtida` ON `curtidas` (\n  `alvo`,\n  `autor`\n)"
  ],
  "listRule": "",
  "viewRule": "",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id",
  "updateRule": null,
  "deleteRule": "@request.auth.id = autor",
  "options": {}
 },
 {
  "id": "7a5v0l954zbf12o",
  "name": "denuncias",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "wwgqh6my",
    "name": "alvo",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 15,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "iama52il",
    "name": "tipo",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 20,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "ijqoo2if",
    "name": "motivo",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 500,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "ipdxgorr",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   }
  ],
  "indexes": [],
  "listRule": "@request.auth.autor = true",
  "viewRule": "@request.auth.autor = true",
  "createRule": "@request.auth.id != \"\" && @request.data.autor = @request.auth.id",
  "updateRule": null,
  "deleteRule": "@request.auth.autor = true",
  "options": {}
 },
 {
  "id": "f2ugz09oqjg1i4i",
  "name": "diretas",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "l6cuvf9i",
    "name": "de",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "ca3g2ct2",
    "name": "para",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "1lriwkkf",
    "name": "texto",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 4000,
     "pattern": ""
    }
   }
  ],
  "indexes": [
   "CREATE INDEX `idx_dm` ON `diretas` (\n  `de`,\n  `para`,\n  `created`\n)"
  ],
  "listRule": "@request.auth.id = de || @request.auth.id = para",
  "viewRule": "@request.auth.id = de || @request.auth.id = para",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.de = @request.auth.id && @request.data.para != @request.auth.id && @request.data.para.banido != true",
  "updateRule": null,
  "deleteRule": "@request.auth.id = de",
  "options": {}
 },
 {
  "id": "31bur6851ndivyu",
  "name": "mensagens",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "2kcqpotr",
    "name": "canal",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "3968ayh8jbvsqxx",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "mldivddw",
    "name": "texto",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 4000,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "exc0v0ja",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "u3tcjoiq",
    "name": "resposta",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 15,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "tu6kbawh",
    "name": "imagem",
    "type": "file",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "mimeTypes": [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/gif"
     ],
     "thumbs": null,
     "maxSelect": 1,
     "maxSize": 5242880,
     "protected": false
    }
   },
   {
    "system": false,
    "id": "rcgpnlgm",
    "name": "editado",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   }
  ],
  "indexes": [
   "CREATE INDEX `idx_msg_canal` ON `mensagens` (\n  `canal`,\n  `created`\n)"
  ],
  "listRule": "autor.banido != true",
  "viewRule": "autor.banido != true",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id && (@collection.config.so_aprovados = false || @request.auth.aprovado = true || @request.auth.autor = true) && (@request.data.canal.so_autor != true || @request.auth.autor = true)",
  "updateRule": "@request.auth.id = autor && @request.auth.banido != true && @request.data.autor:isset = false && @request.data.canal:isset = false",
  "deleteRule": "@request.auth.id = autor || @request.auth.autor = true",
  "options": {}
 },
 {
  "id": "7jhtiun9qmz1twj",
  "name": "qarchis",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "gkoymonf",
    "name": "nome",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 140,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "eygydrdq",
    "name": "descricao",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 2000,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "nwi5jykg",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "vzd0rmze",
    "name": "arquivos",
    "type": "file",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
     "mimeTypes": [],
     "thumbs": null,
     "maxSelect": 30,
     "maxSize": 524288000,
     "protected": false
    }
   },
   {
    "system": false,
    "id": "hxy1osuy",
    "name": "aprovado",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   }
  ],
  "indexes": [],
  "listRule": "aprovado = true || @request.auth.autor = true || @request.auth.id = autor",
  "viewRule": "aprovado = true || @request.auth.autor = true || @request.auth.id = autor",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id && @request.data.aprovado:isset = false",
  "updateRule": "@request.auth.autor = true",
  "deleteRule": "@request.auth.id = autor || @request.auth.autor = true",
  "options": {}
 },
 {
  "id": "b3s174t20smox2p",
  "name": "reacoes",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "h1tgcryv",
    "name": "mensagem",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 15,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "dkld8j3s",
    "name": "emoji",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 8,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "sezudvir",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   }
  ],
  "indexes": [
   "CREATE UNIQUE INDEX `idx_reacao` ON `reacoes` (\n  `mensagem`,\n  `emoji`,\n  `autor`\n)"
  ],
  "listRule": "",
  "viewRule": "",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id",
  "updateRule": null,
  "deleteRule": "@request.auth.id = autor",
  "options": {}
 },
 {
  "id": "b82nfjdv97n1bm8",
  "name": "respostas",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "lfglvy3u",
    "name": "topico",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "4bxcdijgvcec3u1",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "wtkl7slr",
    "name": "texto",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 20000,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "vbo9l5d7",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   }
  ],
  "indexes": [],
  "listRule": "autor.banido != true && topico.autor.banido != true",
  "viewRule": "autor.banido != true && topico.autor.banido != true",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id && (@collection.config.so_aprovados = false || @request.auth.aprovado = true || @request.auth.autor = true)",
  "updateRule": null,
  "deleteRule": "@request.auth.id = autor || @request.auth.autor = true",
  "options": {}
 },
 {
  "id": "4bxcdijgvcec3u1",
  "name": "topicos",
  "type": "base",
  "system": false,
  "schema": [
   {
    "system": false,
    "id": "aopdifvx",
    "name": "titulo",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 140,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "xxnc6hvx",
    "name": "texto",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 20000,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "t8pkljoy",
    "name": "categoria",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "min": null,
     "max": 40,
     "pattern": ""
    }
   },
   {
    "system": false,
    "id": "2n46hb6e",
    "name": "autor",
    "type": "relation",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
     "collectionId": "_pb_users_auth_",
     "cascadeDelete": false,
     "minSelect": null,
     "maxSelect": 1,
     "displayFields": null
    }
   },
   {
    "system": false,
    "id": "ovwlveud",
    "name": "fixado",
    "type": "bool",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {}
   }
  ],
  "indexes": [],
  "listRule": "autor.banido != true",
  "viewRule": "autor.banido != true",
  "createRule": "@request.auth.id != \"\" && @request.auth.banido != true && @request.data.autor = @request.auth.id && (@collection.config.so_aprovados = false || @request.auth.aprovado = true || @request.auth.autor = true) && @request.data.fixado:isset = false",
  "updateRule": "@request.auth.autor = true",
  "deleteRule": "@request.auth.id = autor || @request.auth.autor = true",
  "options": {}
 }
];
  dao.importCollections(snapshot.map((c) => new Collection(c)), false, null);

  const vazio = (nome) => dao.findRecordsByFilter(nome, "id != ''", "", 1, 0).length === 0;
  if (vazio("canais")) {
    const col = dao.findCollectionByNameOrId("canais");
    [["avisos-do-autor", "Novidades de Ailig Qarchi. Só o autor escreve aqui.", true], ["apresente-se", "Diga quem você é, de onde lê e como achou Wallace Ross.", false], ["conversa-geral", "Sobre a série, sobre livros, sobre a vida.", false], ["teorias", "Teorias e perguntas sobre o que já foi lido. Marque spoilers com ||assim||.", false], ["fan-art", "Desenhos, mapas, cartões e tudo o que a obra inspirar.", false], ["ideias", "Ideias para a série, o site e a comunidade.", false]].forEach((c, i) => {
      const r = new Record(col);
      r.set("nome", c[0]); r.set("descricao", c[1]); r.set("ordem", i); r.set("so_autor", c[2]);
      dao.saveRecord(r);
    });
  }
  if (vazio("config")) {
    const r = new Record(dao.findCollectionByNameOrId("config"));
    r.set("regras_texto", "1. Respeito sempre. Nada de ataques, preconceito, assédio ou ameaças.\n2. Nada de pirataria: o livro completo é vendido na Amazon. Qarchis só com conteúdo que você tem o direito de compartilhar.\n3. Spoilers do livro completo vão marcados no título com [SPOILER].\n4. Nada de dados pessoais seus ou de outras pessoas (endereço, telefone, documentos).\n5. O autor modera. Quem quebrar as regras pode ter posts apagados ou ser removido."); r.set("aviso", ""); r.set("so_aprovados", false);
    r.set("qarchis_de_membros", true); r.set("categorias", ["Avisos do autor", "Wallace Ross", "Teorias e perguntas", "Leituras em grupo", "Qarchis", "Conversa livre"]);
    dao.saveRecord(r);
  }
  // conta do autor (usuário ailigqarchi), com a senha que o "Ligar Comunidade" pediu
  const senha = $os.getenv("AUTOR_SENHA");
  let autor = null;
  try { autor = dao.findAuthRecordByUsername("users", "ailigqarchi"); } catch (e) {}
  if (!autor && senha) {
    autor = new Record(dao.findCollectionByNameOrId("users"));
    autor.setUsername("ailigqarchi"); autor.setPassword(senha);
    autor.set("name", "Ailig Qarchi"); autor.set("sobre", "Autor de Wallace Ross.");
  }
  if (autor) { autor.set("autor", true); autor.set("aprovado", true); autor.set("banido", false); dao.saveRecord(autor); }
}, (db) => null);
