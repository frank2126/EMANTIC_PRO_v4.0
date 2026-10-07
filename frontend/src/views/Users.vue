<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>👥</span> Gestión de Usuarios</h1>
      <button class="btn-primary" @click="showForm = !showForm">
        {{ showForm ? '✕ Cancelar' : '+ Nuevo Usuario' }}
      </button>
    </div>

    <div class="stats-row">
      <div class="stat-chip"><span class="sc-val">{{ users.length }}</span><span class="sc-lbl">Total</span></div>
      <div class="stat-chip active"><span class="sc-val">{{ activeCount }}</span><span class="sc-lbl">Activos</span></div>
      <div class="stat-chip admin"><span class="sc-val">{{ adminCount }}</span><span class="sc-lbl">Admins</span></div>
      <div class="stat-chip tech"><span class="sc-val">{{ tecnicoCount }}</span><span class="sc-lbl">Técnicos</span></div>
    </div>

    <transition name="slide">
      <div v-if="showForm" class="card form-card">
        <h3 class="card-title">➕ Crear nuevo usuario</h3>
        <div class="form-grid">
          <div class="fgroup">
            <label class="label">Nombre completo *</label>
            <input v-model="form.name" class="input" placeholder="Ej: Juan Pérez" />
          </div>
          <div class="fgroup">
            <label class="label">Usuario * <span class="hint-txt">(sin espacios)</span></label>
            <input v-model="form.username" class="input" placeholder="juanperez" autocomplete="off"
              @input="form.username = form.username.toLowerCase().replace(/\s/g,'')" />
          </div>
          <div class="fgroup">
            <label class="label">Email</label>
            <input v-model="form.email" type="email" class="input" placeholder="juan@empresa.com" />
          </div>
          <div class="fgroup">
            <label class="label">Rol *</label>
            <select v-model="form.role" class="input">
              <option value="tecnico">🔧 Técnico — Consulta y carga</option>
              <option value="admin">👑 Administrador — Acceso total</option>
            </select>
          </div>
          <div class="fgroup form-full">
            <label class="label">Contraseña * <span class="hint-txt">(mín. 8 chars, 1 mayúscula, 1 número)</span></label>
            <div class="pass-wrap">
              <input v-model="form.password" :type="showPass?'text':'password'" class="input"
                placeholder="Contraseña segura" autocomplete="new-password" />
              <button class="pass-btn" type="button" @click="showPass=!showPass">{{ showPass?'🙈':'👁' }}</button>
            </div>
            <div v-if="form.password" class="strength-row">
              <div class="strength-bar"><div class="strength-fill" :style="{width:strengthPct+'%',background:strengthColor}"></div></div>
              <span class="strength-lbl" :style="{color:strengthColor}">{{ strengthLabel }}</span>
            </div>
          </div>
        </div>

        <div class="perms-box">
          <p class="perms-title">Permisos del rol seleccionado:</p>
          <div class="perms-grid">
            <div v-for="p in permsByRole" :key="p.label" class="perm-item" :class="p.allowed?'perm-yes':'perm-no'">
              <span>{{ p.allowed?'✅':'❌' }}</span><span>{{ p.label }}</span>
            </div>
          </div>
        </div>

        <p v-if="formErr" class="err-msg">⚠ {{ formErr }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showForm=false; resetForm()">Cancelar</button>
          <button class="btn-primary" :disabled="creating" @click="createUser">
            {{ creating ? 'Creando...' : '✅ Crear Usuario' }}
          </button>
        </div>
      </div>
    </transition>

    <div v-if="loading" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando usuarios...</p></div>
    <div v-else class="card users-card">
      <div class="table-top">
        <span class="table-count">{{ users.length }} usuario{{ users.length!==1?'s':'' }}</span>
        <input v-model="search" class="input search-input" placeholder="🔍 Buscar..." />
      </div>
      <div class="table-wrap">
        <table class="utable">
          <thead>
            <tr><th>Usuario</th><th>Email</th><th>Rol</th><th>Estado</th><th>Creado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in filteredUsers" :key="u.id" :class="{inactive:!u.active}">
              <td>
                <div class="u-cell">
                  <div class="u-avatar" :style="{background:roleColor(u.role)}">{{ u.name.charAt(0).toUpperCase() }}</div>
                  <div><div class="u-name">{{ u.name }}</div><div class="u-user">@{{ u.username }}</div></div>
                </div>
              </td>
              <td class="td-email">{{ u.email||'—' }}</td>
              <td><span class="badge" :class="u.role==='admin'?'badge-success':'badge-info'">{{ u.role==='admin'?'👑 Admin':'🔧 Técnico' }}</span></td>
              <td><span class="badge" :class="u.active?'badge-success':'badge-gray'">{{ u.active?'● Activo':'○ Inactivo' }}</span></td>
              <td class="td-date">{{ formatDate(u.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button v-if="u.username!=='admin'" class="btn-tbl" :class="u.active?'btn-warn':'btn-ok'" @click="toggle(u.username,u.active)">
                    {{ u.active?'🔒 Bloquear':'🔓 Activar' }}
                  </button>
                  <button v-if="u.username!=='admin'" class="btn-tbl btn-del" @click="del(u.username)">🗑 Eliminar</button>
                  <span v-if="u.username==='admin'" class="protected">🛡 Protegido</span>
                </div>
              </td>
            </tr>
            <tr v-if="filteredUsers.length===0">
              <td colspan="6" class="td-empty">No se encontraron usuarios</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card perms-table-card">
      <h3 class="card-title">📋 Tabla completa de permisos por rol</h3>
      <div class="table-wrap">
        <table class="ptable">
          <thead><tr><th>Permiso</th><th>🔧 Técnico</th><th>👑 Administrador</th></tr></thead>
          <tbody>
            <tr v-for="p in ALL_PERMS" :key="p.label">
              <td>{{ p.label }}</td>
              <td class="tc">{{ p.tecnico?'✅':'❌' }}</td>
              <td class="tc">✅</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const users=ref([]),loading=ref(true),creating=ref(false)
const showForm=ref(false),formErr=ref(''),showPass=ref(false),search=ref('')
const form=ref({name:'',username:'',email:'',role:'tecnico',password:''})

const activeCount  = computed(()=>users.value.filter(u=>u.active).length)
const adminCount   = computed(()=>users.value.filter(u=>u.role==='admin').length)
const tecnicoCount = computed(()=>users.value.filter(u=>u.role==='tecnico').length)
const filteredUsers = computed(()=>{
  if(!search.value) return users.value
  const s=search.value.toLowerCase()
  return users.value.filter(u=>u.name.toLowerCase().includes(s)||u.username.toLowerCase().includes(s)||(u.email||'').toLowerCase().includes(s))
})
const strengthPct=computed(()=>{const p=form.value.password;let s=0;if(p.length>=8)s+=25;if(p.length>=12)s+=15;if(/[A-Z]/.test(p))s+=20;if(/[0-9]/.test(p))s+=20;if(/[^A-Za-z0-9]/.test(p))s+=20;return Math.min(s,100)})
const strengthColor=computed(()=>strengthPct.value<40?'#ef4444':strengthPct.value<70?'#f59e0b':'#10b981')
const strengthLabel=computed(()=>strengthPct.value<40?'Débil':strengthPct.value<70?'Moderada':'Fuerte ✅')
const permsByRole=computed(()=>{const a=form.value.role==='admin';return[{label:'Ver y subir manuales',allowed:true},{label:'Eliminar manuales',allowed:a},{label:'Crear órdenes mantenimiento',allowed:true},{label:'Eliminar órdenes',allowed:a},{label:'Subir documentación',allowed:true},{label:'Eliminar documentación',allowed:a},{label:'Ver recursos de taller',allowed:true},{label:'Ver analíticas Power BI',allowed:true},{label:'Gestionar usuarios',allowed:a}]})
const ALL_PERMS=[{label:'Ver manuales técnicos',tecnico:true},{label:'Subir nuevos manuales PDF',tecnico:true},{label:'Eliminar manuales',tecnico:false},{label:'Ver mantenimiento',tecnico:true},{label:'Crear órdenes de mantenimiento',tecnico:true},{label:'Completar órdenes',tecnico:true},{label:'Eliminar órdenes',tecnico:false},{label:'Ver y subir documentación',tecnico:true},{label:'Eliminar documentos',tecnico:false},{label:'Ver recursos de taller',tecnico:true},{label:'Ver analíticas Power BI',tecnico:true},{label:'Gestionar usuarios',tecnico:false},{label:'Bloquear / Activar usuarios',tecnico:false},{label:'Eliminar usuarios',tecnico:false}]
const roleColor=r=>r==='admin'?'linear-gradient(135deg,#0d5c45,#1a7fbf)':'linear-gradient(135deg,#1a7fbf,#2db87a)'
const formatDate=d=>{try{return new Date(d).toLocaleDateString('es-CO')}catch{return d||'—'}}
const resetForm=()=>{form.value={name:'',username:'',email:'',role:'tecnico',password:''};formErr.value=''}
const load=async()=>{loading.value=true;try{users.value=(await axios.get('/api/users')).data}catch{}finally{loading.value=false}}
const createUser=async()=>{
  formErr.value=''
  if(!form.value.name){formErr.value='El nombre es obligatorio';return}
  if(!form.value.username){formErr.value='El usuario es obligatorio';return}
  if(!form.value.password||form.value.password.length<8){formErr.value='La contraseña debe tener al menos 8 caracteres';return}
  creating.value=true
  try{await axios.post('/api/users',form.value);showForm.value=false;resetForm();await load()}
  catch(e){formErr.value=e.response?.data?.detail||'Error al crear el usuario'}
  finally{creating.value=false}
}
const toggle=async(username,active)=>{
  if(!confirm(`¿${active?'Bloquear':'Activar'} al usuario "${username}"?`))return
  try{await axios.patch(`/api/users/${username}/toggle`);await load()}
  catch(e){alert(e.response?.data?.detail||'Error')}
}
const del=async username=>{
  if(!confirm(`⚠️ ¿Eliminar permanentemente a "${username}"?\nEsta acción no se puede deshacer.`))return
  try{await axios.delete(`/api/users/${username}`);await load()}
  catch(e){alert(e.response?.data?.detail||'Error')}
}
onMounted(load)
</script>

<style scoped>
.stats-row{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;}
.stat-chip{background:#fff;border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;min-width:80px;box-shadow:var(--shadow);}
.stat-chip.active{border-color:#a7f3d0;}.stat-chip.admin{border-color:#bfdbfe;}.stat-chip.tech{border-color:#bae6fd;}
.sc-val{font-size:24px;font-weight:800;display:block;}.sc-lbl{font-size:11px;color:var(--text-muted);font-weight:600;}
.form-card{padding:24px;margin-bottom:24px;}.card-title{font-size:16px;font-weight:700;margin-bottom:16px;}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;}.form-full{grid-column:1/-1;}
.fgroup{display:flex;flex-direction:column;gap:6px;}.hint-txt{font-size:11px;color:var(--text-muted);font-weight:400;text-transform:none;letter-spacing:0;}
.pass-wrap{position:relative;}.pass-wrap .input{padding-right:44px;}.pass-btn{position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;font-size:16px;opacity:0.5;}
.strength-row{display:flex;align-items:center;gap:10px;margin-top:6px;}.strength-bar{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden;}
.strength-fill{height:100%;transition:width 0.3s,background 0.3s;}.strength-lbl{font-size:12px;font-weight:600;min-width:80px;}
.perms-box{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px;}
.perms-title{font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;}
.perms-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;}
.perm-item{display:flex;align-items:center;gap:8px;font-size:12px;padding:6px 10px;border-radius:6px;}
.perm-yes{background:#d1fae5;color:#065f46;}.perm-no{background:#f1f5f9;color:#94a3b8;}
.err-msg{color:var(--danger);font-size:13px;margin-bottom:12px;background:#fee2e2;padding:10px 14px;border-radius:8px;}
.form-actions{display:flex;gap:10px;justify-content:flex-end;}
.users-card{overflow:hidden;margin-bottom:24px;}
.table-top{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border);background:#f8fafc;gap:16px;}
.table-count{font-size:13px;color:var(--text-muted);font-weight:600;white-space:nowrap;}.search-input{max-width:220px;padding:8px 12px;font-size:13px;}
.table-wrap{overflow-x:auto;}
.utable{width:100%;border-collapse:collapse;}
.utable th{padding:11px 16px;background:#f8fafc;font-size:11px;font-weight:700;color:var(--text-muted);text-align:left;border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;}
.utable td{padding:14px 16px;font-size:13px;border-bottom:1px solid var(--border);vertical-align:middle;}
.utable tr:last-child td{border-bottom:none;}.utable tr:hover td{background:#f8fafc;}.utable tr.inactive td{opacity:0.55;}
.u-cell{display:flex;align-items:center;gap:10px;}
.u-avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:#fff;flex-shrink:0;}
.u-name{font-weight:600;}.u-user{font-size:11px;color:var(--text-muted);font-family:monospace;}
.td-email{color:var(--text-muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.td-date{color:var(--text-muted);font-size:12px;white-space:nowrap;}
.row-actions{display:flex;gap:6px;flex-wrap:wrap;}
.btn-tbl{padding:5px 12px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all 0.15s;white-space:nowrap;font-family:inherit;}
.btn-ok{background:#d1fae5;color:#065f46;}.btn-ok:hover{background:#10b981;color:#fff;}
.btn-warn{background:#fef3c7;color:#92400e;}.btn-warn:hover{background:#f59e0b;color:#fff;}
.btn-del{background:#fee2e2;color:var(--danger);}.btn-del:hover{background:var(--danger);color:#fff;}
.protected{font-size:12px;color:var(--text-muted);}.td-empty{text-align:center;color:var(--text-muted);padding:40px;}
.perms-table-card{padding:24px;}
.ptable{width:100%;border-collapse:collapse;}
.ptable th{padding:10px 16px;background:#f8fafc;font-size:11px;font-weight:700;color:var(--text-muted);text-align:left;border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:0.5px;}
.ptable td{padding:10px 16px;font-size:13px;border-bottom:1px solid #f1f5f9;}.ptable tr:last-child td{border-bottom:none;}
.tc{text-align:center;font-size:15px;}
@media(max-width:900px){.form-grid{grid-template-columns:1fr;}.td-email,.td-date{display:none;}}
</style>
